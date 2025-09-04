{{- define "myapp.name" -}}
myapp
{{- end -}}

{{- define "myapp.fullname" -}}
{{ printf "%s" (include "myapp.name" .) }}
{{- end -}}
