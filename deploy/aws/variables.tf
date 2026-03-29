variable "db_password" {
  description = "Password for RDS PostgreSQL"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "gps_trace_api_token" {
  description = "GPS-Trace API Token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openweathermap_api_key" {
  description = "OpenWeatherMap API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "iot_api_key" {
  description = "IoT Gateway API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "traffic_api_key" {
  description = "Traffic API Key (Google/HERE/Mapbox)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "glih_admin_password" {
  description = "Seed password for admin@glih.ops account (force_password_change=true on first login)"
  type        = string
  sensitive   = true
}

variable "glih_dispatcher_password" {
  description = "Seed password for sample dispatcher accounts (force_password_change=true on first login)"
  type        = string
  sensitive   = true
}

variable "dispatcher_admin_password" {
  description = "Password for legacy dispatcher admin login (DISPATCHER_ADMIN_PASSWORD)"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "HS256 JWT signing secret — must be at least 32 characters"
  type        = string
  sensitive   = true
}

# Phase 1-3 MCP connector secrets
variable "samsara_api_key" {
  description = "Samsara ELD / Predictive Maintenance API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "dat_username" {
  description = "DAT Load Board username"
  type        = string
  sensitive   = true
  default     = ""
}

variable "dat_password" {
  description = "DAT Load Board password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tms_endpoint" {
  description = "TMS integration REST API endpoint"
  type        = string
  default     = ""
}

variable "tms_api_key" {
  description = "TMS integration API key (McLeod/Oracle)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "geofence_api_key" {
  description = "Geofencing API key (Google Maps / HERE)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "eia_api_key" {
  description = "EIA fuel prices API key (optional — public API)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "port_status_api_key" {
  description = "Port status API key (MarineTraffic/Portcast)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "twilio_account_sid" {
  description = "Twilio account SID for POD notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "twilio_auth_token" {
  description = "Twilio auth token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "twilio_from_number" {
  description = "Twilio source phone number for SMS"
  type        = string
  default     = ""
}

variable "insurance_endpoint" {
  description = "Insurance claims API endpoint (Riskonnect/custom)"
  type        = string
  default     = ""
}

variable "insurance_api_key" {
  description = "Insurance claims API key"
  type        = string
  sensitive   = true
  default     = ""
}
