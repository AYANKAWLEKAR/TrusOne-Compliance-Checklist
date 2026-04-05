export type SourceCitation = {
  source_id: string;
  source_type: string;
  title: string;
  url?: string | null;
  excerpt?: string | null;
};

export type TaskDetail = {
  explanation: string;
  next_step: string;
  why_it_matters: string;
  notes: string;
};

export type TaskItem = {
  id: string;
  title: string;
  source: string;
  source_url?: string | null;
  priority_label: string;
  meta_label: string;
  default_completed: boolean;
  citations: string[];
  detail: TaskDetail;
};

export type ComplianceReportSummary = {
  analysis_text: string;
  total_tasks: number;
  completed_tasks: number;
  open_tasks: number;
  mapped_sources: string[];
};

export type ComplianceReportResponse = {
  summary: ComplianceReportSummary;
  tasks: TaskItem[];
  sources: SourceCitation[];
};

export type ComplianceReportRequest = {
  location: string;
  industry: string;
  company_size: string;
  compliance_status?: string;
  location_city?: string;
  location_county?: string;
  location_state?: string;
};

export type ComplianceLocationOption = {
  value: string;
  display_label: string;
  city: string;
  county: string;
  state: string;
  aliases: string[];
};

export type ComplianceOptionsResponse = {
  industries: string[];
  locations: ComplianceLocationOption[];
};

export type GeoIPResponse = {
  city?: string | null;
  region?: string | null;
  postal?: string | null;
  country_name?: string | null;
  formatted_location: string;
};
