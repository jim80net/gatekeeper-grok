#!/bin/sh
set -eu

root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)

check() {
  file=$1
  tool=$2
  key=$3
  jq -e --arg tool "$tool" --arg key "$key" '
    .hookEventName == "pre_tool_use" and
    .toolName == $tool and
    (.toolInput | has($key)) and
    (.toolInput[$key] | type == "string")
  ' "$root/fixtures/stdin/$file" >/dev/null
  printf 'PASS %-46s %s.%s\n' "$file" "$tool" "$key"
}

check pre_tool_use_shell_live.json Shell command
check pre_tool_use_run_terminal_command.json run_terminal_command command
check pre_tool_use_read_file.json read_file target_file
check pre_tool_use_search_replace.json search_replace file_path
check pre_tool_use_write.json write file_path
check pre_tool_use_list_dir.json list_dir target_directory
check pre_tool_use_grep.json grep pattern
check pre_tool_use_web_fetch.json web_fetch url

printf '\n8 verified Grok tool shapes; WebSearch remains explicitly unverified.\n'
