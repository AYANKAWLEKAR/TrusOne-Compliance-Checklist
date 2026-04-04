export type SourceCitation = {
  source_id: string;
  source_type: string;
  title: string;
  url?: string | null;
  excerpt?: string | null;
};

export type ComplianceRequirement = {
  regulation_id: string;
  certification_clause: string;
  business_activity: string;
  citations: string[];
};

export type RegulatoryDependency = {
  primary_agency: string;
  related_agency: string;
  relationship: string;
  citations: string[];
};

export type RequiredDocument = {
  document_type: string;
  description: string;
  required_by: string;
  citations: string[];
};

export type RequiredWorkflow = {
  workflow_name: string;
  description: string;
  frequency: string;
  responsible_party: string;
  citations: string[];
};

export type ComplianceReportResponse = {
  compliance_certification_requirements: ComplianceRequirement[];
  regulatory_dependencies: RegulatoryDependency[];
  required_documents: RequiredDocument[];
  required_workflows: RequiredWorkflow[];
  sources: SourceCitation[];
};

export type ComplianceReportRequest = {
  location: string;
  industry: string;
  company_size: string;
};

export type GeoIPResponse = {
  city?: string | null;
  region?: string | null;
  postal?: string | null;
  country_name?: string | null;
  formatted_location: string;
};
