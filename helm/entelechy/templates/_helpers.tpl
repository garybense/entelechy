{{/*
Expand the name of the chart.
*/}}
{{- define "entelechy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "entelechy.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
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
{{- define "entelechy.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "entelechy.labels" -}}
helm.sh/chart: {{ include "entelechy.chart" . }}
{{ include "entelechy.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "entelechy.selectorLabels" -}}
app.kubernetes.io/name: {{ include "entelechy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "entelechy.api.labels" -}}
{{ include "entelechy.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "entelechy.api.selectorLabels" -}}
{{ include "entelechy.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Control plane labels
*/}}
{{- define "entelechy.controlPlane.labels" -}}
{{ include "entelechy.labels" . }}
app.kubernetes.io/component: control-plane
{{- end }}

{{/*
Control plane selector labels
*/}}
{{- define "entelechy.controlPlane.selectorLabels" -}}
{{ include "entelechy.selectorLabels" . }}
app.kubernetes.io/component: control-plane
{{- end }}

{{/*
Worker labels
*/}}
{{- define "entelechy.worker.labels" -}}
{{ include "entelechy.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "entelechy.worker.selectorLabels" -}}
{{ include "entelechy.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "entelechy.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "entelechy.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate database URL
*/}}
{{- define "entelechy.databaseUrl" -}}
{{- if .Values.databaseUrl }}
{{- .Values.databaseUrl }}
{{- else if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s-postgresql:%d/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "entelechy.fullname" .) (.Values.postgresql.service.port | int) .Values.postgresql.auth.database }}
{{- else }}
{{- printf "postgresql://%s:$(POSTGRES_PASSWORD)@%s:%d/%s" .Values.postgresql.external.username .Values.postgresql.external.host (.Values.postgresql.external.port | int) .Values.postgresql.external.database }}
{{- end }}
{{- end }}

{{/*
API URL for control plane
*/}}
{{- define "entelechy.apiUrl" -}}
{{- printf "http://%s-api:%d" (include "entelechy.fullname" .) (.Values.api.service.port | int) }}
{{- end }}

{{/*
TEI reranker labels
*/}}
{{- define "entelechy.tei.reranker.labels" -}}
{{ include "entelechy.labels" . }}
app.kubernetes.io/component: tei-reranker
{{- end }}

{{/*
TEI reranker selector labels
*/}}
{{- define "entelechy.tei.reranker.selectorLabels" -}}
{{ include "entelechy.selectorLabels" . }}
app.kubernetes.io/component: tei-reranker
{{- end }}

{{/*
TEI embedding labels
*/}}
{{- define "entelechy.tei.embedding.labels" -}}
{{ include "entelechy.labels" . }}
app.kubernetes.io/component: tei-embedding
{{- end }}

{{/*
TEI embedding selector labels
*/}}
{{- define "entelechy.tei.embedding.selectorLabels" -}}
{{ include "entelechy.selectorLabels" . }}
app.kubernetes.io/component: tei-embedding
{{- end }}

{{/*
Get the name of the secret to use
*/}}
{{- define "entelechy.secretName" -}}
{{- if .Values.existingSecret }}
{{- .Values.existingSecret }}
{{- else }}
{{- printf "%s-secret" (include "entelechy.fullname" .) }}
{{- end }}
{{- end }}
