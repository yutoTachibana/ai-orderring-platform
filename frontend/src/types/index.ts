export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'sales' | 'engineer'
}

export interface Company {
  id: number
  name: string
  company_type: 'client' | 'vendor' | 'ses'
  address: string | null
  phone: string | null
  email: string | null
  website: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SkillTag {
  id: number
  name: string
  category: string
}

export interface Engineer {
  id: number
  full_name: string
  email: string
  phone: string | null
  company_id: number | null
  company: Company | null
  employment_type: 'proper' | 'first_tier_proper' | 'freelancer' | 'first_tier_freelancer'
  subcontracting_tier: number
  hourly_rate: number | null
  monthly_rate: number | null
  availability_status: 'available' | 'assigned' | 'unavailable'
  years_of_experience: number | null
  skills: SkillTag[]
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  name: string
  description: string | null
  client_company_id: number | null
  client_company: Company | null
  status: 'draft' | 'open' | 'in_progress' | 'completed' | 'closed'
  subcontracting_tier_limit: 'proper_only' | 'first_tier' | 'second_tier' | 'no_restriction' | null
  start_date: string | null
  end_date: string | null
  budget: number | null
  required_headcount: number | null
  required_skills: SkillTag[]
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Quotation {
  id: number
  project_id: number
  project: Project | null
  engineer_id: number
  engineer: Engineer | null
  unit_price: number
  estimated_hours: number
  total_amount: number
  status: 'draft' | 'submitted' | 'approved' | 'rejected'
  submitted_at: string | null
  approved_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Order {
  id: number
  quotation_id: number
  quotation: Quotation | null
  order_number: string
  status: 'pending' | 'confirmed' | 'cancelled'
  confirmed_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Contract {
  id: number
  order_id: number
  contract_number: string
  contract_type: 'quasi_delegation' | 'contract' | 'dispatch'
  engineer_id: number
  engineer: Engineer | null
  project_id: number
  project: Project | null
  start_date: string
  end_date: string
  monthly_rate: number
  min_hours: number | null
  max_hours: number | null
  status: 'draft' | 'active' | 'expired' | 'terminated'
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Invoice {
  id: number
  contract_id: number
  contract: Contract | null
  invoice_number: string
  billing_month: string
  working_hours: number
  base_amount: number
  adjustment_amount: number
  tax_amount: number
  total_amount: number
  status: 'draft' | 'sent' | 'paid' | 'overdue'
  sent_at: string | null
  paid_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ProcessingJob {
  id: number
  slack_message_id: string | null
  slack_channel_id: string | null
  excel_file_path: string | null
  status: 'received' | 'parsing' | 'routing' | 'pending_approval' | 'executing' | 'completed' | 'failed'
  assigned_system: string | null
  approved_by: number | null
  approved_at: string | null
  result: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
  logs: ProcessingLog[]
}

export interface ProcessingLog {
  id: number
  job_id: number
  step_name: string
  status: string
  message: string
  screenshot_path: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}
