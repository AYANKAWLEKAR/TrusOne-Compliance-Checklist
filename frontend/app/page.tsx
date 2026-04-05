"use client";

import React, {
  FormEvent,
  ReactNode,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  createComplianceReport,
  fetchComplianceOptions,
  resolveGeoIP,
} from "@/lib/api";
import {
  ComplianceLocationOption,
  ComplianceReportResponse,
  GeoIPResponse,
  TaskItem,
} from "@/lib/types";

type TaskFilter = "all" | "pending" | "done";

type ComboboxOption = {
  id: string;
  value: string;
  label: string;
  displayLabel: string;
  groupLabel?: string | null;
  searchText: string;
  aliases?: string[];
  city?: string;
  county?: string;
  state?: string;
};

const FALLBACK_LOCATION_OPTIONS: ComboboxOption[] = [
  locationOptionFromApi({
    value: "Berkeley, California",
    display_label: "Berkeley, California",
    city: "Berkeley",
    county: "Alameda County",
    state: "California",
    aliases: ["Berkeley", "Berkeley, CA"],
  }),
  locationOptionFromApi({
    value: "Unincorporated Areas, Alameda County, California",
    display_label: "Unincorporated Areas, Alameda County, California",
    city: "Unincorporated Areas",
    county: "Alameda County",
    state: "California",
    aliases: ["Unincorporated", "Unincorporated Alameda County"],
  }),
];

const FALLBACK_INDUSTRY_OPTIONS: ComboboxOption[] = [
  makeOption(
    "chemical",
    "Chemical",
    "Chemical",
    "Supported in live DB",
    [
      "chemical manufacturing",
      "petrochemicals",
      "specialty chemicals",
      "hazmat",
      "chemical storage",
    ],
  ),
];

const COMPANY_SIZE_OPTIONS: ComboboxOption[] = [
  {
    id: "size-1-10",
    value: "1-10",
    label: "1 - 10 Employees",
    displayLabel: "1 - 10 Employees",
    groupLabel: null,
    searchText: normalizeText("1 - 10 Employees"),
  },
  {
    id: "size-11-50",
    value: "11-50",
    label: "11 - 50 Employees",
    displayLabel: "11 - 50 Employees",
    groupLabel: null,
    searchText: normalizeText("11 - 50 Employees"),
  },
  {
    id: "size-51-250",
    value: "51-250",
    label: "51 - 250 Employees",
    displayLabel: "51 - 250 Employees",
    groupLabel: null,
    searchText: normalizeText("51 - 250 Employees"),
  },
  {
    id: "size-251-1000",
    value: "251-1000",
    label: "251 - 1,000 Employees",
    displayLabel: "251 - 1,000 Employees",
    groupLabel: null,
    searchText: normalizeText("251 - 1,000 Employees"),
  },
  {
    id: "size-1000-plus",
    value: "1000+",
    label: "1,000+ Employees",
    displayLabel: "1,000+ Employees",
    groupLabel: null,
    searchText: normalizeText("1,000+ Employees"),
  },
];

const INDUSTRY_AI_SYNONYMS: Record<string, string[]> = {
  chemical: ["petrochemicals", "specialty chemicals", "hazmat", "manufacturing"],
  petrochemicals: ["chemical"],
  specialty: ["chemical"],
  manufacturing: ["chemical", "plant", "factory", "production"],
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CITY_CONTEXT_MAP: Record<
  string,
  { county: string; state: string; displayLabel: string; aliases?: string[] }
> = {
  berkeley: {
    county: "Alameda County",
    state: "California",
    displayLabel: "Berkeley, California",
    aliases: ["Berkeley, CA"],
  },
  oakland: {
    county: "Alameda County",
    state: "California",
    displayLabel: "Oakland, California",
    aliases: ["Oakland, CA"],
  },
  "unincorporated areas": {
    county: "Alameda County",
    state: "California",
    displayLabel: "Unincorporated Areas, Alameda County, California",
    aliases: ["Unincorporated", "Unincorporated Alameda County"],
  },
};

export default function HomePage() {
  const [locationOptions, setLocationOptions] = useState<ComboboxOption[]>(
    FALLBACK_LOCATION_OPTIONS,
  );
  const [industryOptions, setIndustryOptions] = useState<ComboboxOption[]>(
    FALLBACK_INDUSTRY_OPTIONS,
  );
  const [location, setLocation] = useState(
    FALLBACK_LOCATION_OPTIONS[0]?.value ?? "",
  );
  const [industry, setIndustry] = useState(
    FALLBACK_INDUSTRY_OPTIONS[0]?.value ?? "",
  );
  const [companySize, setCompanySize] = useState("51-250");
  const [complianceStatus, setComplianceStatus] = useState("");
  const [report, setReport] = useState<ComplianceReportResponse | null>(null);
  const [completionState, setCompletionState] = useState<Record<string, boolean>>(
    {},
  );
  const [activeFilter, setActiveFilter] = useState<TaskFilter>("all");
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [workEmail, setWorkEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState("");
  const [locationStatusIsError, setLocationStatusIsError] = useState(false);
  const [justCompletedTaskId, setJustCompletedTaskId] = useState<string | null>(null);
  const [customLocationOption, setCustomLocationOption] =
    useState<ComboboxOption | null>(null);
  const completionAnimationTimeoutRef = useRef<number | null>(null);
  const resultsHeadingRef = useRef<HTMLHeadingElement | null>(null);

  const allLocationOptions = customLocationOption
    ? [
        customLocationOption,
        ...locationOptions.filter((option) => option.id !== customLocationOption.id),
      ]
    : locationOptions;

  const selectedLocationOption = useMemo(
    () => allLocationOptions.find((option) => option.value === location) ?? null,
    [allLocationOptions, location],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadOptions() {
      try {
        const response = await fetchComplianceOptions();
        if (cancelled) return;

        const nextLocations = response.locations.map(locationOptionFromApi);
        const nextIndustries =
          response.industries.map((industryName) =>
            makeOption(
              slugify(industryName),
              industryName,
              industryName,
              "Supported in live DB",
              [
                "chemical manufacturing",
                "petrochemicals",
                "specialty chemicals",
                "hazmat",
                "chemical storage",
              ],
            ),
          ) || [];

        if (nextLocations.length) {
          setLocationOptions(nextLocations);
          setLocation((current) =>
            nextLocations.some((option) => option.value === current)
              ? current
              : nextLocations[0].value,
          );
        }

        if (nextIndustries.length) {
          setIndustryOptions(nextIndustries);
          setIndustry((current) =>
            nextIndustries.some((option) => option.value === current)
              ? current
              : nextIndustries[0].value,
          );
        }
      } catch {
        if (cancelled) return;
      }
    }

    void loadOptions();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const rafId = window.requestAnimationFrame(() => {
      document.body.classList.add("motion-ready");
    });

    return () => {
      window.cancelAnimationFrame(rafId);
      document.body.classList.remove("motion-ready");
    };
  }, []);

  useEffect(() => {
    if (!isSubmitting) return undefined;

    setLoadingStep(1);
    const timers = [
      window.setTimeout(() => setLoadingStep(2), 600),
      window.setTimeout(() => setLoadingStep(3), 1200),
    ];

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [isSubmitting]);

  useEffect(() => {
    if (!report || isSubmitting) return;
    resultsHeadingRef.current?.focus();
  }, [report, isSubmitting]);

  useEffect(() => {
    return () => {
      if (completionAnimationTimeoutRef.current !== null) {
        window.clearTimeout(completionAnimationTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const hasOpenModal = Boolean(activeTaskId) || isEmailModalOpen;
    document.body.classList.toggle("modal-open", hasOpenModal);
    return () => {
      document.body.classList.remove("modal-open");
    };
  }, [activeTaskId, isEmailModalOpen]);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (activeTaskId) {
        setActiveTaskId(null);
        return;
      }
      if (isEmailModalOpen) {
        setIsEmailModalOpen(false);
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, [activeTaskId, isEmailModalOpen]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!location || !industry || !companySize) {
      setError("Select location, industry, and company size before generating.");
      return;
    }

    setEmailError(null);
    setIsEmailModalOpen(true);
  }

  async function submitEmailGate() {
    const normalizedEmail = workEmail.trim();
    if (!EMAIL_REGEX.test(normalizedEmail)) {
      setEmailError("Please enter a valid work email address.");
      return;
    }

    setEmailError(null);
    setIsEmailModalOpen(false);
    setIsSubmitting(true);

    try {
      const response = await createComplianceReport({
        location,
        industry,
        company_size: companySize,
        compliance_status: complianceStatus.trim() || undefined,
        location_city: selectedLocationOption?.city || undefined,
        location_county: selectedLocationOption?.county || undefined,
        location_state: selectedLocationOption?.state || undefined,
      });
      setReport(response);
      setCompletionState(
        Object.fromEntries(
          response.tasks.map((task) => [task.id, task.default_completed]),
        ),
      );
      setActiveFilter("all");
      setActiveTaskId(null);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to generate report.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function locateCurrentJurisdiction() {
    setLocationStatus("Locating your jurisdiction...");
    setLocationStatusIsError(false);

    try {
      const response = await resolveGeoIP();
      const matchedOption = findLocationOption(response, allLocationOptions);

      if (matchedOption) {
        setLocation(matchedOption.value);
        setLocationStatus(`Located near ${matchedOption.displayLabel}.`);
        setLocationStatusIsError(false);
        return true;
      }

      const fallbackValue = response.formatted_location.trim();
      const derivedLocation = deriveLocationFromGeo(response);
      if (fallbackValue || derivedLocation) {
        const option =
          derivedLocation ??
          makeOption(
            `detected-${slugify(fallbackValue)}`,
            fallbackValue,
            fallbackValue,
            "Detected",
          );
        setCustomLocationOption(option);
        setLocation(option.value);
        setLocationStatus(`Located near ${option.displayLabel}.`);
        setLocationStatusIsError(false);
        return true;
      }

      setLocationStatus("Unable to determine your location right now.");
      setLocationStatusIsError(true);
      return false;
    } catch (geoError) {
      setLocationStatus(
        geoError instanceof Error
          ? geoError.message
          : "Unable to determine your location right now.",
      );
      setLocationStatusIsError(true);
      return false;
    }
  }

  const tasks = report?.tasks ?? [];
  const activeTask = tasks.find((task) => task.id === activeTaskId) ?? null;
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((task) =>
    isTaskComplete(task, completionState),
  ).length;
  const openTasks = totalTasks - completedTasks;
  const visibleTasks = tasks.filter((task) => {
    const checked = isTaskComplete(task, completionState);
    if (activeFilter === "pending") return !checked;
    if (activeFilter === "done") return checked;
    return true;
  });

  function pulseCompletedTask(taskId: string) {
    setJustCompletedTaskId(taskId);
    if (completionAnimationTimeoutRef.current !== null) {
      window.clearTimeout(completionAnimationTimeoutRef.current);
    }
    completionAnimationTimeoutRef.current = window.setTimeout(() => {
      setJustCompletedTaskId((current) => (current === taskId ? null : current));
      completionAnimationTimeoutRef.current = null;
    }, 460);
  }

  function setTaskCompletion(taskId: string, isComplete: boolean) {
    setCompletionState((current) => ({
      ...current,
      [taskId]: isComplete,
    }));
    if (isComplete) {
      pulseCompletedTask(taskId);
    }
  }

  function toggleTask(taskId: string) {
    setTaskCompletion(taskId, !(completionState[taskId] ?? false));
  }

  return (
    <>
      <header className="top-banner">
        <div className="top-banner-brand">
          <div className="top-banner-logo">T1</div>
          <span className="top-banner-wordmark">TrusOne</span>
        </div>
        <div className="top-banner-center">
          <span className="promo-badge">New</span>
          <span>
            One AI System for All EHS Work — Less manual work. More control.
          </span>
        </div>
        <div className="top-banner-actions">
          <button className="top-banner-btn" type="button">
            Book a Demo
            <ArrowRightIcon />
          </button>
        </div>
      </header>

      <div className="app-wrapper">
        <div className="app-container">
          <form className="card config-panel" onSubmit={onSubmit}>
            <div className="form-stack">
              <div className="form-copy">
                <p className="label-caps">Chemical Compliance MVP</p>
                <h1>Generate a task-ready compliance checklist.</h1>
                <p className="helper-copy">
                  Submit a company profile and synthesize Supabase-backed
                  regulatory guidance into actionable tasks with source-linked
                  detail.
                </p>
              </div>

              <SearchableCombobox
                label="Location"
                icon={<LocationIcon />}
                options={allLocationOptions}
                value={location}
                onChange={setLocation}
                placeholder="Select city"
                searchPlaceholder="Search city"
                statusMessage={locationStatus}
                statusTone={locationStatusIsError ? "error" : "default"}
                actionLabel="Locate my location"
                actionIcon={<SparkIcon />}
                onAction={locateCurrentJurisdiction}
              />

              <SearchableCombobox
                label="Industry"
                icon={<IndustryIcon />}
                options={industryOptions}
                value={industry}
                onChange={setIndustry}
                placeholder="Chemical"
                searchPlaceholder="Search sector or industry"
                aiActionLabel="Search with AI"
                onAiSuggest={getAiIndustrySuggestionIds}
              />

              <SearchableCombobox
                label="Company Size"
                icon={<PeopleIcon />}
                options={COMPANY_SIZE_OPTIONS}
                value={companySize}
                onChange={setCompanySize}
                placeholder="Select company size"
                searchPlaceholder="Search company size"
              />

              <label className="form-group" htmlFor="complianceStatus">
                <span className="label-caps">Current Compliance Status</span>
                <textarea
                  id="complianceStatus"
                  value={complianceStatus}
                  onChange={(event) => setComplianceStatus(event.target.value)}
                  placeholder="Describe your current compliance situation, e.g. 'We have basic OSHA training but no formal documentation. Recently received a warning about waste handling procedures...'"
                />
              </label>
            </div>

            <button className="btn-primary btn-primary--wide" type="submit">
              <SparkIcon />
              Generate Analysis
            </button>

            {error ? (
              <div className="form-error" role="alert">
                {error}
              </div>
            ) : null}
          </form>

          <main className="results-panel">
            {isSubmitting ? (
              <div className="loading-state" role="status" aria-live="polite">
                <div className="progress-steps">
                  {[
                    "Analyzing regulatory requirements...",
                    "Mapping compliance obligations...",
                    "Generating action items...",
                  ].map((label, index) => {
                    const stepNumber = index + 1;
                    const isDone = loadingStep > stepNumber;
                    const isActive = loadingStep === stepNumber;
                    return (
                      <div
                        className={`progress-step${isActive ? " active" : ""}${
                          isDone ? " done" : ""
                        }`}
                        key={label}
                      >
                        <div className="step-indicator">
                          <div className="spinner-wrapper">
                            <div className="spinner" />
                          </div>
                          <CheckIcon />
                        </div>
                        <span>{label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {!isSubmitting && !report ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <TagIcon />
                </div>
                <h3>Generate Your Compliance Report</h3>
                <p>
                  Select your location, industry, and company size, then click
                  Generate Analysis to receive a personalized compliance
                  checklist powered by AI.
                </p>
              </div>
            ) : null}

            {!isSubmitting && report ? (
              <div className="results-content visible">
                <div className="summary-grid">
                  <div className="card metric-card">
                    <div>
                      <div className="label-caps">Open Work</div>
                      <div className="metric-large">{openTasks}</div>
                      <p className="metric-note">
                        Priority items remaining across the synthesized
                        compliance obligations for this company profile.
                      </p>
                    </div>
                    <div>
                      <div
                        className="progress-meter"
                        aria-label={`${completedTasks} of ${totalTasks} tasks completed`}
                      >
                        <div
                          className="progress-meter-bar"
                          style={{
                            width: `${totalTasks ? (completedTasks / totalTasks) * 100 : 0}%`,
                          }}
                        />
                      </div>
                      <div className="label-sm metric-footer">
                        {completedTasks} completed of {totalTasks}
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h2 className="section-heading">
                      <SparkIcon />
                      <span id="resultsHeading" ref={resultsHeadingRef} tabIndex={-1}>
                        AI Regulatory Analysis
                      </span>
                    </h2>
                    <p className="ai-text">{report.summary.analysis_text}</p>
                    <div className="sources-tags">
                      <span className="label-caps sources-label">Mapped:</span>
                      {report.summary.mapped_sources.map((source) => (
                        <span className="tag" key={source}>
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="card checklist-card">
                  <div className="checklist-header">
                    <h2>Compliance Requirements</h2>
                    <div className="segment-control" aria-label="Filter requirements">
                      {(["all", "pending", "done"] as const).map((filter) => (
                        <button
                          key={filter}
                          className={`segment-btn${
                            activeFilter === filter ? " active" : ""
                          }`}
                          data-filter={filter}
                          type="button"
                          aria-pressed={activeFilter === filter}
                          onClick={() => setActiveFilter(filter)}
                        >
                          {filter === "all"
                            ? "All"
                            : filter === "pending"
                              ? "Pending"
                              : "Done"}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="list-header label-caps">
                    <div />
                    <div>Requirement</div>
                    <div className="source-column">Source</div>
                  </div>

                  <div className="list-items">
                    {visibleTasks.length ? (
                      visibleTasks.map((task) => {
                        const checked = isTaskComplete(task, completionState);
                        return (
                          <div
                            className={`list-item${checked ? " checked" : ""}${
                              justCompletedTaskId === task.id ? " just-completed" : ""
                            }`}
                            data-task-id={task.id}
                            key={task.id}
                          >
                            <button
                              className="custom-checkbox"
                              type="button"
                              onClick={() => toggleTask(task.id)}
                              aria-label={`Mark ${task.title} complete`}
                            >
                              <span className="custom-checkbox-indicator">
                                {checked ? <CheckIcon /> : null}
                              </span>
                            </button>

                            <button
                              className="task-trigger"
                              type="button"
                              onClick={() => setActiveTaskId(task.id)}
                              aria-haspopup="dialog"
                              aria-controls="task-detail-modal"
                            >
                              <span className="task-title">{task.title}</span>
                              <span className="task-meta">
                                <span>{task.priority_label}</span>
                                <span className="task-meta-dot" />
                                <span>{task.meta_label}</span>
                              </span>
                            </button>

                            <div className="task-source">{task.source}</div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="empty-filter-state">
                        No tasks match the current filter.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </main>
        </div>
      </div>

      <EmailCaptureModal
        isOpen={isEmailModalOpen}
        email={workEmail}
        error={emailError}
        onChangeEmail={setWorkEmail}
        onClose={() => setIsEmailModalOpen(false)}
        onSubmit={submitEmailGate}
      />

      <TaskDetailModal
        task={activeTask}
        onClose={() => setActiveTaskId(null)}
        onComplete={
          activeTask
            ? () => {
                if (!isTaskComplete(activeTask, completionState)) {
                  setTaskCompletion(activeTask.id, true);
                }
              }
            : undefined
        }
        isCompleted={activeTask ? isTaskComplete(activeTask, completionState) : false}
      />
    </>
  );
}

function SearchableCombobox({
  label,
  icon,
  options,
  value,
  onChange,
  placeholder,
  searchPlaceholder,
  statusMessage,
  statusTone = "default",
  actionLabel,
  actionIcon,
  onAction,
  aiActionLabel,
  onAiSuggest,
}: {
  label: string;
  icon: ReactNode;
  options: ComboboxOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  searchPlaceholder: string;
  statusMessage?: string;
  statusTone?: "default" | "error";
  actionLabel?: string;
  actionIcon?: ReactNode;
  onAction?: () => Promise<boolean> | boolean;
  aiActionLabel?: string;
  onAiSuggest?: (query: string, options: ComboboxOption[]) => string[];
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [aiSuggestionIds, setAiSuggestionIds] = useState<string[]>([]);
  const [aiStatusMessage, setAiStatusMessage] = useState("");
  const [aiStatusTone, setAiStatusTone] = useState<"default" | "error">("default");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const labelId = useId();
  const searchId = useId();

  const selectedOption = options.find((option) => option.value === value) ?? null;
  const exactMatch = hasExactOptionMatch(options, query);
  const filteredOptions = aiSuggestionIds.length
    ? options.filter((option) => aiSuggestionIds.includes(option.id))
    : getFilteredOptions(options, query);
  const visibleStatusMessage = aiStatusMessage || statusMessage || "";
  const visibleStatusTone = aiStatusMessage ? aiStatusTone : statusTone;
  const shouldShowAiAction = Boolean(
    aiActionLabel &&
      onAiSuggest &&
      query.trim().length > 0 &&
      !exactMatch &&
      !aiSuggestionIds.length,
  );

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event: MouseEvent) => {
      if (
        rootRef.current &&
        event.target instanceof Node &&
        !rootRef.current.contains(event.target)
      ) {
        setOpen(false);
        setQuery("");
        setAiSuggestionIds([]);
        setAiStatusMessage("");
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    searchInputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const nextActiveId =
      filteredOptions.find((option) => option.id === activeId)?.id ??
      filteredOptions[0]?.id ??
      null;
    if (nextActiveId !== activeId) {
      setActiveId(nextActiveId);
    }
  }, [activeId, filteredOptions, open]);

  function closeCombobox() {
    setOpen(false);
    setQuery("");
    setAiSuggestionIds([]);
    setAiStatusMessage("");
  }

  function moveActive(direction: number) {
    if (!filteredOptions.length) return;
    const currentIndex = filteredOptions.findIndex((option) => option.id === activeId);
    const safeIndex = currentIndex === -1 ? 0 : currentIndex;
    const nextIndex =
      (safeIndex + direction + filteredOptions.length) % filteredOptions.length;
    setActiveId(filteredOptions[nextIndex]?.id ?? null);
  }

  async function handleAction() {
    if (!onAction) return;
    const shouldClose = await onAction();
    if (shouldClose) {
      closeCombobox();
    }
  }

  function handleAiSuggest() {
    if (!onAiSuggest) return;
    const suggestionIds = onAiSuggest(query, options);
    setAiSuggestionIds(suggestionIds);
    if (suggestionIds.length) {
      setActiveId(suggestionIds[0] ?? null);
      setAiStatusMessage(`AI suggestions for "${query.trim()}"`);
      setAiStatusTone("default");
      return;
    }

    setAiStatusMessage(`No close AI match for "${query.trim()}". Try another phrase.`);
    setAiStatusTone("error");
  }

  return (
    <div className="form-group">
      <span className="label-caps" id={labelId}>
        {label}
      </span>
      <div className={`input-wrapper combobox${open ? " open" : ""}`} ref={rootRef}>
        <span className="icon combobox-leading-icon" aria-hidden="true">
          {icon}
        </span>
        <button
          className="combobox-trigger"
          type="button"
          aria-labelledby={labelId}
          aria-label={`${label}: ${selectedOption?.displayLabel ?? placeholder}`}
          aria-haspopup="listbox"
          aria-expanded={open}
          onClick={() => {
            if (open) {
              closeCombobox();
              return;
            }
            setOpen(true);
            setActiveId(selectedOption?.id ?? options[0]?.id ?? null);
          }}
        >
          <span
            className={`combobox-trigger-value${
              selectedOption ? "" : " combobox-trigger-placeholder"
            }`}
          >
            {selectedOption?.displayLabel ?? placeholder}
          </span>
        </button>
        <span className="combobox-trigger-icon" aria-hidden="true">
          <ChevronDownIcon />
        </span>

        {open ? (
          <div className="combobox-panel">
            <input
              className="combobox-search"
              id={searchId}
              ref={searchInputRef}
              type="text"
              placeholder={searchPlaceholder}
              value={query}
              aria-label={`${label} search`}
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={open}
              onChange={(event) => {
                setQuery(event.target.value);
                setAiSuggestionIds([]);
                setAiStatusMessage("");
              }}
              onKeyDown={(event) => {
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  moveActive(1);
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  moveActive(-1);
                } else if (event.key === "Enter") {
                  event.preventDefault();
                  if (!activeId) return;
                  const activeOption = filteredOptions.find(
                    (option) => option.id === activeId,
                  );
                  if (activeOption) {
                    onChange(activeOption.value);
                    closeCombobox();
                  }
                } else if (event.key === "Escape") {
                  event.preventDefault();
                  closeCombobox();
                }
              }}
            />

            {actionLabel ? (
              <div className="combobox-actions">
                <button className="combobox-action" type="button" onClick={handleAction}>
                  <span className="icon combobox-action-icon" aria-hidden="true">
                    {actionIcon}
                  </span>
                  {actionLabel}
                </button>
              </div>
            ) : null}

            {visibleStatusMessage ? (
              <p
                className={`combobox-status${
                  visibleStatusTone === "error" ? " is-error" : ""
                }`}
              >
                {visibleStatusMessage}
              </p>
            ) : null}

            <div className="combobox-options" role="listbox" aria-labelledby={labelId}>
              {filteredOptions.length ? (
                renderComboboxOptions({
                  options: filteredOptions,
                  activeId,
                  selectedId: selectedOption?.id ?? null,
                  onSelect: (option) => {
                    onChange(option.value);
                    closeCombobox();
                  },
                })
              ) : (
                <div className="combobox-empty">No matching options found.</div>
              )}
            </div>

            {shouldShowAiAction ? (
              <button
                className="combobox-action combobox-action--full"
                type="button"
                onClick={handleAiSuggest}
              >
                {aiActionLabel}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function EmailCaptureModal({
  isOpen,
  email,
  error,
  onChangeEmail,
  onClose,
  onSubmit,
}: {
  isOpen: boolean;
  email: string;
  error: string | null;
  onChangeEmail: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const rafId = window.requestAnimationFrame(() => setVisible(true));
    return () => window.cancelAnimationFrame(rafId);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className={`modal-overlay${visible ? " visible" : ""}`}
      aria-hidden="false"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal modal--email"
        role="dialog"
        aria-modal="true"
        aria-labelledby="email-modal-title"
        aria-describedby="email-modal-description"
      >
        <div className="modal-header">
          <div>
            <div className="email-modal-icon" aria-hidden="true">
              <DocumentIcon />
            </div>
            <h3 className="email-modal-title" id="email-modal-title">
              Get your personalized compliance report
            </h3>
            <p className="email-modal-subtitle" id="email-modal-description">
              Enter your work email and we&apos;ll generate a tailored analysis
              based on your profile, plus deliver a full PDF report to your
              inbox.
            </p>
          </div>
          <button
            className="modal-close"
            type="button"
            onClick={onClose}
            aria-label="Close email prompt"
          >
            <CloseIcon />
          </button>
        </div>

        <div className="email-modal-perks">
          {[
            "Full PDF compliance report delivered to your email",
            "Actionable items mapped to regulatory bodies",
            "AI-powered analysis updated with latest regulations",
          ].map((perk) => (
            <div className="email-perk" key={perk}>
              <span className="email-perk-icon" aria-hidden="true">
                <CheckIcon />
              </span>
              {perk}
            </div>
          ))}
        </div>

        <div className="email-field-group">
          <label className="label-caps" htmlFor="emailInput">
            Work Email
          </label>
          <input
            id="emailInput"
            type="email"
            value={email}
            placeholder="you@company.com"
            autoComplete="email"
            inputMode="email"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "emailError" : undefined}
            onChange={(event) => onChangeEmail(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                onSubmit();
              }
            }}
          />
          {error ? (
            <p className="field-error" id="emailError" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className="modal-actions">
          <button className="btn-secondary" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-modal-primary" type="button" onClick={onSubmit}>
            Generate Report
          </button>
        </div>

        <div className="email-modal-trust">
          <LockIcon />
          Your data is secure. We never share your email with third parties.
        </div>
      </div>
    </div>
  );
}

function TaskDetailModal({
  task,
  onClose,
  onComplete,
  isCompleted,
}: {
  task: TaskItem | null;
  onClose: () => void;
  onComplete?: () => void;
  isCompleted: boolean;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!task) return;
    const rafId = window.requestAnimationFrame(() => setVisible(true));
    return () => window.cancelAnimationFrame(rafId);
  }, [task]);

  if (!task) return null;

  return (
    <div
      className={`modal-overlay${visible ? " visible" : ""}`}
      aria-hidden="false"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal modal-task-detail"
        id="task-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-detail-title"
      >
        <div className="modal-header">
          <div>
            <div className="modal-kicker">Requirement Detail</div>
            <h3 id="task-detail-title">{task.title}</h3>
          </div>
          <button
            className="modal-close"
            type="button"
            onClick={onClose}
            aria-label="Close task detail"
          >
            <CloseIcon />
          </button>
        </div>

        <div className="modal-task-meta">
          <span className="label-caps">Source</span>
          {task.source_url ? (
            <a
              className="source-link-button"
              href={task.source_url}
              target="_blank"
              rel="noreferrer"
            >
              <ExternalLinkIcon />
              <span>{task.source}</span>
            </a>
          ) : (
            <span className="source-link-button is-static">{task.source}</span>
          )}
        </div>

        <div className="modal-task-divider" />

        <div className="modal-task-body">
          <ModalSection title="Explanation">
            {task.detail.explanation}
          </ModalSection>
          <ModalSection title="Immediate Next Step">
            {task.detail.next_step}
          </ModalSection>
          <ModalSection title="Why It Matters">
            {task.detail.why_it_matters}
          </ModalSection>
          <ModalSection title="Source / Retention Notes">
            {task.detail.notes}
          </ModalSection>
        </div>

        <div className="modal-task-divider" />

        <div className="modal-task-footer">
          <button className="btn-secondary" type="button" onClick={onClose}>
            Close
          </button>
          <button
            className="btn-modal-primary"
            type="button"
            onClick={onComplete}
            disabled={isCompleted}
          >
            {isCompleted ? "Marked Complete" : "Mark as Complete"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ModalSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="modal-task-section">
      <h4 className="modal-section-title">{title}</h4>
      <p>{children}</p>
    </div>
  );
}

function renderComboboxOptions({
  options,
  activeId,
  selectedId,
  onSelect,
}: {
  options: ComboboxOption[];
  activeId: string | null;
  selectedId: string | null;
  onSelect: (option: ComboboxOption) => void;
}) {
  let previousGroup: string | null = null;

  return options.flatMap((option) => {
    const nodes: ReactNode[] = [];
    if (option.groupLabel && option.groupLabel !== previousGroup) {
      previousGroup = option.groupLabel;
      nodes.push(
        <div
          className="combobox-group-label"
          key={`${option.groupLabel}-${option.id}-label`}
        >
          {option.groupLabel}
        </div>,
      );
    }

    nodes.push(
      <button
        className={`combobox-option${
          activeId === option.id ? " is-active" : ""
        }${selectedId === option.id ? " is-selected" : ""}`}
        key={option.id}
        role="option"
        aria-selected={selectedId === option.id}
        type="button"
        onMouseDown={(event) => event.preventDefault()}
        onClick={() => onSelect(option)}
      >
        <span className="combobox-option-label">{option.displayLabel}</span>
        {option.groupLabel ? (
          <span className="combobox-option-meta">{option.groupLabel}</span>
        ) : null}
      </button>,
    );

    return nodes;
  });
}

function getFilteredOptions(options: ComboboxOption[], query: string) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return options;

  return options.filter((option) => {
    const aliasMatch = (option.aliases ?? []).some((alias) =>
      normalizeText(alias).includes(normalizedQuery),
    );
    return option.searchText.includes(normalizedQuery) || aliasMatch;
  });
}

function hasExactOptionMatch(options: ComboboxOption[], query: string) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return false;

  return options.some(
    (option) =>
      normalizeText(option.label) === normalizedQuery ||
      normalizeText(option.value) === normalizedQuery,
  );
}

function getAiIndustrySuggestionIds(query: string, options: ComboboxOption[]) {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) return [];

  return options
    .map((option) => ({
      id: option.id,
      score: scoreIndustryOption(option, normalizedQuery),
    }))
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 5)
    .map((entry) => entry.id);
}

function scoreIndustryOption(option: ComboboxOption, normalizedQuery: string) {
  const queryTokens = normalizedQuery.split(" ").filter(Boolean);
  const optionTokens = new Set(option.searchText.split(" ").filter(Boolean));
  let score = 0;

  if (option.searchText.includes(normalizedQuery)) score += 12;

  queryTokens.forEach((token) => {
    if (optionTokens.has(token)) score += 4;
    (INDUSTRY_AI_SYNONYMS[token] ?? []).forEach((synonym) => {
      if (option.searchText.includes(normalizeText(synonym))) {
        score += 3;
      }
    });
  });

  return score;
}

function findLocationOption(
  response: GeoIPResponse,
  options: ComboboxOption[],
): ComboboxOption | null {
  const responseParts = [response.city, response.region].filter(Boolean).join(" ");
  const normalizedResponse = normalizeText(
    responseParts || response.formatted_location || "",
  );

  if (!normalizedResponse) return null;

  return (
    options.find((option) => option.searchText.includes(normalizedResponse)) ??
    options.find((option) => normalizedResponse.includes(normalizeText(option.value))) ??
    options.find((option) =>
      (option.aliases ?? []).some((alias) =>
        normalizedResponse.includes(normalizeText(alias)),
      ),
    ) ??
    null
  );
}

function locationOptionFromApi(option: ComplianceLocationOption): ComboboxOption {
  return {
    id: slugify(`${option.city}-${option.county}-${option.state}`),
    value: option.value,
    label: option.display_label,
    displayLabel: option.display_label,
    groupLabel: "City",
    searchText: normalizeText(
      [option.display_label, option.city, option.county, option.state, ...option.aliases].join(
        " ",
      ),
    ),
    aliases: option.aliases,
    city: option.city,
    county: option.county,
    state: option.state,
  };
}

function deriveLocationFromGeo(response: GeoIPResponse): ComboboxOption | null {
  const city = response.city?.trim();
  const region = response.region?.trim();

  if (!city) return null;

  const known = CITY_CONTEXT_MAP[city.toLowerCase()];
  if (known) {
    return {
      ...makeOption(
        `detected-${slugify(city)}`,
        known.displayLabel,
        known.displayLabel,
        "City",
        known.aliases ?? [],
      ),
      city,
      county: known.county,
      state: known.state,
    };
  }

  if (region) {
    const displayLabel = `${city}, ${region}`;
    return {
      ...makeOption(
        `detected-${slugify(displayLabel)}`,
        displayLabel,
        displayLabel,
        "City",
        [`${city}, ${region}`],
      ),
      city,
      county: "",
      state: region,
    };
  }

  return null;
}

function makeOption(
  id: string,
  value: string,
  displayLabel: string,
  groupLabel?: string | null,
  aliases: string[] = [],
): ComboboxOption {
  return {
    id,
    value,
    label: displayLabel,
    displayLabel,
    groupLabel,
    aliases,
    searchText: normalizeText([displayLabel, value, groupLabel, ...aliases].join(" ")),
  };
}

function normalizeText(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function slugify(value: string) {
  return normalizeText(value).replace(/\s+/g, "-");
}

function isTaskComplete(
  task: TaskItem,
  completionState: Record<string, boolean>,
): boolean {
  return completionState[task.id] ?? task.default_completed;
}

function SparkIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2v4" />
      <path d="M12 18v4" />
      <path d="M4.93 4.93l2.83 2.83" />
      <path d="M16.24 16.24l2.83 2.83" />
      <path d="M2 12h4" />
      <path d="M18 12h4" />
      <path d="M4.93 19.07l2.83-2.83" />
      <path d="M16.24 7.76l2.83-2.83" />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 21s-6-4.35-6-10a6 6 0 1 1 12 0c0 5.65-6 10-6 10Z" />
      <circle cx="12" cy="11" r="2.5" />
    </svg>
  );
}

function IndustryIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 21h18" />
      <path d="M5 21V7l7-4v18" />
      <path d="M12 11h7v10" />
      <path d="M8 10h1" />
      <path d="M8 14h1" />
      <path d="M8 18h1" />
      <path d="M15 14h1" />
      <path d="M15 18h1" />
    </svg>
  );
}

function PeopleIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
      <path d="M16 13H8" />
      <path d="M16 17H8" />
      <path d="M10 9H8" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14" />
      <path d="M12 5l7 7-7 7" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 3h7v7" />
      <path d="M10 14 21 3" />
      <path d="M21 14v4a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3h4" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function TagIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 5H2v7l6.29 6.29a2.42 2.42 0 0 0 3.42 0l3.58-3.58a2.42 2.42 0 0 0 0-3.42L9 5Z" />
      <circle cx="6" cy="9" r="1" />
      <path d="M22 5 17.5 9.5" />
      <path d="M17 2v6" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 6l12 12" />
      <path d="M18 6 6 18" />
    </svg>
  );
}
