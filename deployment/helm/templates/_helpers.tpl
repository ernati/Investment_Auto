{{/*
Expand the name of the chart.
*/}}
{{- define "investment-auto.name" -}}
{{- default .Chart.Name .Values.app.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "investment-auto.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.app.name }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "investment-auto.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "investment-auto.labels" -}}
helm.sh/chart: {{ include "investment-auto.chart" . }}
{{ include "investment-auto.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "investment-auto.selectorLabels" -}}
app.kubernetes.io/name: {{ include "investment-auto.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "investment-auto.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "investment-auto.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database host
*/}}
{{- define "investment-auto.databaseHost" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" .Release.Name }}
{{- else if .Values.zalandoPostgresql.enabled }}
{{- printf "app-db.%s.svc.cluster.local" .Release.Namespace }}
{{- else }}
{{- .Values.config.database.host }}
{{- end }}
{{- end }}

{{/*
Database secret name
*/}}
{{- define "investment-auto.databaseSecretName" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-db-secret" (include "investment-auto.fullname" .) }}
{{- else }}
{{- printf "%s-db-secret" (include "investment-auto.fullname" .) }}
{{- end }}
{{- end }}

{{/*
KIS secret name
*/}}
{{- define "investment-auto.kisSecretName" -}}
{{- printf "%s-kis-secret" (include "investment-auto.fullname" .) }}
{{- end }}

{{/*
ConfigMap name
*/}}
{{- define "investment-auto.configMapName" -}}
{{- printf "%s-config" (include "investment-auto.fullname" .) }}
{{- end }}
