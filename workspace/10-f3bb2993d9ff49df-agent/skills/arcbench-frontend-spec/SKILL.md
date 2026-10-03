---
name: arcbench-frontend-spec
description: Frontend interaction design specification for ARC Bench applications. Read before implementing UI code (buttons, menus, dialogs, notifications, hover behavior, forms) so the generated interface follows consistent accessibility, predictability, and feedback-semantics rules.
---

# ARC Bench Frontend Interaction Specification

Design rules for the application's interactive UI. Follow these rules when implementing or
modifying frontend interaction code. The rules are task-independent: they describe how a
well-formed interface should behave, not how any particular scenario is checked.

## When to Use

Apply when the module touches frontend interaction: buttons, menus, dialogs, notifications,
hover behavior, forms, or keyboard handling. Pure backend modules can skip this skill.

## Rules

### A. Accessibility-Tree Residency (hover-revealed controls)

Interactive controls that are revealed on hover/focus (action rows, icon buttons, menus)
MUST stay inside the accessibility tree at all times. Reveal them with `opacity` only —
never `visibility`/`display` — and never unmount them while their owning card/list item is
mounted.

- Why: the platform's strict locators resolve `getByRole` against the accessibility tree.
  `visibility:hidden` / `display:none` removes the control from that tree, so a card-scoped
  `card.getByRole('button', ...)` only matches while the pointer happens to be exactly on the
  card — hover-timing fragility that passes or fails by luck. `opacity:0` keeps the control
  in the tree at all times; hover only changes its visual appearance. Duplicate same-named
  controls across cards are fine: strict locators are card-scoped, so they never collide.
- Good: `opacity-0 group-hover:opacity-100 group-focus-within:opacity-100`.
- Avoid: `invisible group-hover:visible`, `hidden group-hover:flex`, mount-on-hover.

### B. Exact Accessible Names (strict-locator contract)

Every interactive control a test may target must have an accessible name that EXACTLY equals
the name the requirement scenario text quotes for it (e.g. "Take a note", "Settings",
"Undo", "Archive", "More options", "Pin note", "Change color", "Note editor", "Search",
"Work", "Reminders", "Toggle sidebar"). The platform's strict locators match
`getByRole(role, { name: /^<name>$/i })` — anchored and case-insensitive — so one extra
suffix, prefix, ellipsis or colon kills the match.

- **Where the name comes from**: the requirement scenario text (the quoted string) is
  authoritative. A screenshot's visible text is NOT — screenshots show the real product,
  which may decorate the label (e.g. Google Keep shows "Take a note..."). When the quoted
  name and the visible text differ, use the quoted name for the accessible name.
- **No decorations in the accessible name**: no "..." (ellipsis), no ": <detail>" suffix,
  no "— <detail>" suffix, no extra " menu"/" button"/" note" suffix, no "Open ..." prefix.
  Decorative detail belongs in visible text / placeholder / `title`, never in `aria-label`
  or in the element's text when that text IS the accessible name.
- **Icon buttons** carry `aria-label` with the exact name. A visible-text button gets the
  exact name either by writing the exact text or by an `aria-label` that overrides it
  (e.g. visible "Take a note..." + `aria-label="Take a note"`).
- **Duplicate names are fine when strict locators scope the query** to one container
  (`card.getByRole('button', ...)`). Do not "fix" duplicates by renaming with suffixes.
- Avoid: `aria-label="Settings menu"` for a button the test calls "Settings";
  `aria-label="Undo: Note trashed"` for a button the test calls "Undo";
  a clickable button whose only accessible name is the text "Take a note..." (no exact-name
  `aria-label`).

### C. Explicit Action Feedback

Destructive or state-changing actions (delete, archive, restore, clear, ...) must be followed
by a notification that states the action and its result, and should offer an undo entry point.
Dialog primary actions must use a verb (Save / Delete / Apply) and provide a cancel path.

- Why: feedback must be recognizable as an explicit outcome; vague wording is not feedback.
- Good: "Note deleted" with an Undo action; dialog primary "Save" with "Cancel" beside it.
- Avoid: "Note trashed" when the action is a delete; a dialog whose confirm button has no verb.

### D. Compatibility with the E2E Locator Resolver

ARC-Bench Playwright helpers resolve controls against the accessibility tree using
**exact roles and anchored names**: `getByRole(role, { name: /^<exact name>$/i })`, scoped
to a container (card/dialog/sidebar) when the app renders repeated items. Matching is
case-insensitive but NOT substring: one extra word, ellipsis or suffix kills the match, and
a control hidden with `visibility`/`display` is not in the tree at all. Because this
convention is shared across every ARC-Bench app, these rules generalize beyond any single
task:

1. **Dialog/menu options: match the official role semantics.**
   When the requirement text describes an option the user selects/clears (e.g. `select the
   "Work" label`, `clear the selected label`), render it as a native `checkbox`
   (`<input type="checkbox" aria-label={name}>`) inside the dialog; the strict suite asserts
   exactly that role (`getByRole('dialog', ...).getByRole('checkbox', {name:...})`), so a
   button-simulated checkbox never matches. When the text describes an action (e.g. "Delete
   Note", "Save"), render a `button`. Give the dialog itself the exact name the requirement
   implies (e.g. "Note editor"), and keep only one dialog with that name open at a time.
2. **Names come from the requirement text; no field-name shadowing; no decorated names.**
   - The accessible name of any control a scenario quotes must equal that quoted name
     verbatim (rule B). A search box the text calls "Search" is named "Search", and form
     fields use the exact quoted labels (e.g. "Title", "Note content") — never decorated
     variants like "Take a note...".
   - Do not put a form-field's exact name on a non-form container (`form`, `li`, `div`,
     `span`, `toolbar`, `group`, `aside`, `complementary`) or on a global control (search
     box, filter, cart): that makes an exact-name field lookup ambiguous, and a container
     whose aria-label contains the field word resolves `getByLabel(/word/i)` to the
     container instead of the real control.
   - **Field word roots** (match case-insensitively) that commonly name form fields:
     Description, Name, Tags, Title, Content, Email, Password, Search, Note, Book, Shelf,
     Page, Draft, Chapter, Label, Address, City, Country, Phone, Zip/Postal, Alias, Cart,
     Favorites, Details. A non-form control carrying one of these roots in its accessible
     name is a defect.
   - **A data-entry `<form>`'s own aria-label (rule E1) must share NO word with any field
     label inside it.** The field resolver tries `getByLabel(/word/i)` first and keeps the
     first hit in document order, and an ancestor always precedes its descendants — so a
     container named after a field inside it wins the lookup and `fill()` dies with
     "Element is not an <input>". Renaming is not a fix unless the word is dropped
     entirely: "Address form" → "Address details" still shadows the "Address" field.
     Avoid `"Header search"` (shadows a "Search" input), `"Address details"`, `"New review"`
     (shadows a "Review" field); use names outside the field vocabulary — `"Catalog lookup"`,
     `"Recipient information"`, `"Your feedback"`. The gate runs this check as
     `label-shadowing` and blocks on any hit.
   - **List-row wrappers must not repeat the row's entity name**: a `<li>`/`<div>` around
     a list row must not carry `aria-label={entityName}` — that makes
     `getByLabel(/Name/i).first()` resolve to the non-clickable wrapper instead of the
     row's link/button. Put the name on the interactive element itself.
   - **Dialog names must be the plain exact name** ("Note editor"), never a
     "Note editor: <title>" / "Note editor — <title>" pattern — suffix patterns break
     `getByRole('dialog', {name:...})` anchors.
3. **Modals must not unmount with their trigger.**
   Mount modal dialogs via a portal at the top level (or keep the dialog state at page
   level), never inside a list-item component that a filter/search can remove. If a list
   re-render unmounts the card hosting the editor, unsaved edits are silently discarded.

### E. Form & Branding Semantics

1. **Every data-entry `<form>` must have a unique accessible name.** Add `aria-label`
   (or `aria-labelledby` pointing at a visible heading) — e.g. `<form aria-label="Login
   form">`. Unnamed forms are a gate-blocking defect: tests resolve
   `getByRole('form', {name:...})` against them. The name must simultaneously satisfy
   rule D.2's word-disjointness (no word shared with a field label inside the form) —
   a named form that shadows its own field is equally gate-blocking under
   `label-shadowing`.
2. **The brand logo must be locatable by BOTH `button` and `link` role
   queries.** The strict suite may resolve the logo as
   `getByRole('button', {name: /logo/i})` OR as `getByRole('link', ...)` — the
   requirement text usually quotes only the logo's name ("BookStack logo"), never
   its role. A bare `<a aria-label="BookStack logo" href="/">` answers only the
   link query and fails the button query (observed: bookstack REQ-1.2/6.1.2/7.1/
   7.2/9.1 all resolved the logo as `button`). Cover both:
   - Preferred: `<a href="/" role="button" aria-label="BookStack logo">` — link
     semantics with an explicit button role, so `getByRole('button')` and
     `getByRole('link')` both match.
   - Acceptable: `<button aria-label="BookStack logo" onClick={...home}>`.
   - Avoid: a bare `<a>` with no `role="button"` — the button query finds
     nothing, and the click targets the same page either way.
   Keep "logo" in the accessible name; do not put the only name-bearing text in
   a `hidden`/`sm:hidden` span (it disappears under small viewports) or
   `aria-hidden` it, and do not rely on a `title` attribute alone (it is not
   part of the accessible name).
3. **List items (notes, shelves, books, chapters, pages, posts) must expose the entity
   name in their accessible name.** Render the name as link/button text (or in its
   `aria-label`); do not `aria-hidden` the name span.
4. **Form-field labels must use the common field word** so both substring and exact-name
   queries match: main name field → label "Name"; description → "Description"; tags →
   "Tags"; title → "Title". A label like "Page title" does not match `getByLabel(/Name/i)`.
5. **The logo dual-role pattern (E.2) is for the LOGO ONLY — do not generalize
   `<a role="button">` to every navigation entry.** The official resolver tries
   `getByRole('button', {name:/X/i})` FIRST and keeps the first hit in document
   order, so a chrome BUTTON whose accessible name equals a page action's name —
   the login form's "SIGN IN" submit, a filter checkbox, a menu option — can steal
   that click. But this only bites when the suite resolves the name **globally**.
   Rules, in priority order:
   - **A navigation entry inside a landmark (`<nav>`, `<aside>`,
     `role="complementary"`, `role="navigation"`) keeps the `button` role and is
     NEVER demoted to a plain link** whenever the suite resolves that name inside
     the landmark (`getByRole('complementary').getByRole('button',{name:/^Archive$/i})`).
     The gate probe `landmark-roles` blocks on such a demotion.
   - When a global hijack IS proven, prefer fixes that keep every role: make the
     page action win document order (render it before the chrome entry) or give the
     page action its own requirement qualifier. Demote the chrome entry to a plain
     link only when neither is possible AND the name is never resolved as a button
     inside a landmark.
   - Observed both sides: PrestaShop p13 — header `Sign in` with `role="button"`
     preceded the login submit → 12 account/checkout tests failed (a real global
     hijack); keep p20 — the `name-shadow` repair demoted the sidebar
     `Archive`/`Work`/`Reminders` entries to links, every
     `complementary > button` test timed out, 90.6 → 40.6 (an inert collision).
   - The gate probe `name-shadow` blocks on an exact chrome-button ↔ page-action
     collision **only when the parsed official suite proves a global query for that
     name** (or the suite is invisible, in which case the instruction is to reorder
     rather than remove a role); substring overlaps stay advisory.

### F. Assertable Success & State Semantics

1. **After create/save, navigate to the created entity's details page** so its name
   becomes a visible heading (a test asserting the "Page Created X" heading sees it on
   the entity page, not hidden behind a toast or a list redirect). Returning to the
   list hides the created entity from role/heading queries.
2. **Destructive/state-change actions show feedback whose wording matches the action**
   ("deleted", "archived", "restored", "favourited") with an undo entry point where
   applicable; avoid synonyms the tests do not use (a "trashed" note does not satisfy
   `/deleted/i`).
3. **The authenticated homepage must render the state-widget sections the product
   defines** — e.g. "My Recent Drafts", "My Recently Viewed", "My Most Viewed
   Favorites"/"Favourites", "Recently Updated Pages", "Recent Activity". Tests assert
   these section headings and the entities inside them; do not collapse them into one
   generic "Recent" list.
4. **If the reference product uses a collapsible section toggle** (e.g. BookStack's
   "Shelf Tags" collapsible), implement the toggle button plus the collapsible section;
   do not flatten it into a bare labelled input.

### G. Fixture Data Naming: Keyword-Neutral Display Names

User accounts, aliases, wishlist/folder/shelf names, and any other fixture display name
the requirement does NOT quote verbatim are the agent's choice — keep them free of action
verbs and field word roots that tests use as loose locators (delete, remove, edit,
rename, create, update, save, cart, name, address, search, view, ...). Requirements fix
emails and product names; the human-readable name gets rendered in global chrome — the
header full-name link, sidebar, breadcrumb, footer — where a substring locator
(`getByRole('link', {name:/delete/i})`) hits it and steers the test away from the
intended control.

- Why: a header link "Dana Deleter" matches `/delete/i` before the address row's Delete
  button renders; the click navigates to /account instead of deleting (observed:
  PrestaShop REQ-8.4.4/8.6.5/8.6.6; same pattern for "Remy Remover", "Ryan Renamer").
- Good: "Dana Smith", "Remy Martin", "Ryan Brown", "Cathy Green".
- Avoid: "Dana Deleter", "Remy Remover", "Ryan Renamer", "Cathy Carter".
- This does NOT apply to control names a scenario quotes ("Delete", "Rename", "Save"):
  those must keep their exact quoted name (rule B). It applies only to names the agent
  invents.
- Before finishing, run every invented display name against the keyword list and report
  the outcome in the seed evidence ("Dana Smith -> no keyword collision").

### H. Locator-API Scoping: State Indicators Live INSIDE the Card

Playwright locator APIs are scoped to the **subtree** of the locator they are chained
onto. `card.getByTitle('Pinned')` / `card.getByLabel('...')` / `card.getByRole(...)`
match **descendant elements only** — they never match the card element itself, even
when that element carries the `title`/`aria-label` attribute.

- Why: state indicators (pinned / favorited / archived / unread / status) are asserted
  by tests with card-scoped queries such as `expect(card.getByTitle('Pinned')).toBeVisible()`.
  Putting `title="Pinned"` on the card's own `<article>`/`<li>` (observed: keep
  REQ-2.8.1/2.8.3, `NoteCard.tsx` set the title on the article root) matches nothing —
  the element is the root, not a descendant — and the test times out while the state
  is actually correct.
- Good: render the indicator as a **descendant element inside the card**:
  `{note.pinned ? <span className="..." title="Pinned"><PinIcon /></span> : null}`.
  The same holds for `aria-label`-based indicators (`getByLabel`) and for icons the
  test resolves with `getByTitle`.
- `title` is NOT part of the accessible name (E.2 note): `getByRole('button', {name:...})`
  never reads a `title` attribute, so never rely on `title` alone for a control's name.
- The card root's `aria-label`/`title` may still exist for other reasons, but it can
  never substitute for an inner indicator element.

## Self-Check

After implementing frontend interaction code, verify:

1. Hover-only controls stay in the accessibility tree: revealed via `opacity`, never
   `visibility`/`display`-hidden and never unmounted while their owning card is mounted (A).
2. Every control a scenario quotes by name has that exact accessible name — no ellipsis, no
   ": detail" / "— detail" / " menu" / " note" suffix, no decorative prefix (B). Duplicate
   names across repeated cards are fine; icon buttons carry the exact `aria-label` (B).
3. Every state-changing action shows explicit feedback with an undo path where relevant,
   and dialog confirm buttons are verb-labeled with a cancel option.
4. Selectable dialog options (labels/tags/flags) are native `checkbox`es inside a dialog
   with the exact required name; action options are `button`s; no global control (search
   box, filter) carries a form-field's exact name; every modal dialog is mounted
   independently of any list item's lifecycle (D).
5. Every data-entry `<form>` has an `aria-label`; the home logo is locatable by
   both `button` and `link` role queries with "logo" in its accessible name; list
   items expose entity names; field labels use the exact names the scenario text
   quotes (E).
6. No toolbar/group/aside/complementary control carries a field word root in its
   accessible name, and every dialog name is the plain exact name without a
   "label: suffix" / "label — suffix" pattern (D2).
7. Create/save flows land on the created entity's details page; the authenticated
   homepage renders the state-widget sections named by the product (F).
8. No container (form/li/div/section wrapper) accessible name shares any word with a field
   label inside it, and none repeats a row's entity name (D2/E1; the gate probe
   `label-shadowing` blocks on a hit — renaming that keeps the word does not clear it).
9. Every invented fixture display name is keyword-neutral (G).
10. No global chrome entry (header/nav/footer) carries `role="button"` with an accessible
    name that equals a page action's name on the same page (submit / checkbox / option) —
    on colliding pages it is a plain link, so the page action answers the button query
    (E.5; the gate probe `name-shadow` blocks on exact collisions).
11. State indicators (pinned / favorited / archived / status) are rendered as
    **descendant elements inside their card** with the `title`/`aria-label` the tests
    query (`card.getByTitle('Pinned')` matches descendants only — never the card root;
    `title` is not part of the accessible name) (H).
