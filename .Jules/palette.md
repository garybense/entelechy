## 2026-08-26 - Add ARIA Labels to Pagination Icons
**Learning:** Found a recurring pattern in the control-plane data views where Lucide icons are used inside unlabelled Button components for pagination (e.g., ChevronsLeft, ChevronRight). This renders pagination inaccessible to screen readers as they announce as empty buttons.
**Action:** When implementing new data tables or lists with pagination, always ensure icon-only buttons include descriptive `aria-label` attributes (like 'Go to next page' or 'Go to first group').
