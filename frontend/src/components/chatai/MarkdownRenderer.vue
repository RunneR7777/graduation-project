<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css';

interface Props {
  content?: string;
}

const props = defineProps<Props>();

marked.setOptions({
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  gfm: true,
  breaks: true,
});

const renderedContent = computed(() => {
  if (!props.content) return '';
  return marked.parse(props.content);
});
</script>

<style scoped>
.markdown-body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: #1f2937;
}

.markdown-body p {
  margin-bottom: 1em;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: 1.5em 0 0.5em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 {
  font-size: 1.5em;
}

.markdown-body h2 {
  font-size: 1.3em;
}

.markdown-body h3 {
  font-size: 1.1em;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 1.8em;
  margin-bottom: 1em;
}

.markdown-body li {
  margin-bottom: 0.25em;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  background-color: #f3f4f6;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace;
}

.markdown-body pre {
  padding: 16px;
  background-color: #111827;
  color: #e5e7eb;
  border-radius: 10px;
  overflow-x: auto;
  margin-bottom: 1em;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
  font-size: 0.95em;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #e5e7eb;
  padding: 8px 10px;
}

.markdown-body blockquote {
  border-left: 3px solid #2563eb;
  padding-left: 12px;
  color: #4b5563;
  margin: 1em 0;
}
</style>

