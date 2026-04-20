# Material Icons Reference

All icons use the `material-symbols-rounded` font class:
```html
<span class="material-symbols-rounded" style="color:var(--accent);font-size:1.5rem;">icon_name</span>
```

Do not invent icon names. If a concept is not in the recommended list below, verify the name at [fonts.google.com/icons](https://fonts.google.com/icons?icon.style=Rounded&icon.set=Material+Symbols) before using.

---

## Blacklisted Icons

The following names render incorrectly or do not exist in the Material Icons Round font. MUST NOT be used.

| Blocked icon | Problem | Use instead |
|---|---|---|
| `settings_off` | Does not exist in Material Symbols Rounded — falls back to raw text | `toggle_off`, `layers_clear`, or `block` |
| `docker` | Not in Material Symbols library — falls back to a random unrelated glyph | `inventory_2`, `dns`, or `memory` |

---

## Recommended Icons by Concept

| Concept | Icon name |
|---|---|
| **Status / Validation** | |
| Success / done | `check_circle` |
| Error / blocked | `cancel` |
| Warning / caution | `warning` |
| Info | `info` |
| Verified / approved | `verified` |
| Positive sentiment | `thumb_up` |
| New / featured highlight | `new_releases` |
| Top-rated / starred | `star` |
| Milestone / flagged | `flag` |
| Saved / bookmarked | `bookmark` |
| Urgent / high priority | `priority_high` |
| Problem / issue | `report_problem` |
| Task completed | `task_alt` |
| All complete | `done_all` |
| **Data / Analytics** | |
| Analytics / charts | `analytics` |
| Monitoring / pulse | `monitoring` |
| Query / stats | `query_stats` |
| Bar chart | `bar_chart` |
| Stacked bar chart | `stacked_bar_chart` |
| Line graph / trend | `show_chart` |
| Area chart | `area_chart` |
| Pie chart | `pie_chart` |
| Donut / completion % | `donut_large` |
| Bubble chart | `bubble_chart` |
| Scatter / correlation | `scatter_plot` |
| Waterfall analysis | `waterfall_chart` |
| Waveform / signal | `ssid_chart` |
| Ranking / leaderboard | `leaderboard` |
| Growth / increase | `trending_up` |
| Decline | `trending_down` |
| Flat / neutral trend | `trending_flat` |
| Table / data grid | `table_chart` |
| Schema / structure | `schema` |
| Dataset | `dataset` |
| **Cloud / Infrastructure** | |
| Cloud | `cloud` |
| Cloud complete / synced | `cloud_done` |
| Upload to cloud | `cloud_upload` |
| Download from cloud | `cloud_download` |
| Cloud sync | `cloud_sync` |
| Queued jobs | `cloud_queue` |
| Server / DNS | `dns` |
| Storage | `storage` |
| Compute / memory | `memory` |
| Package / container | `inventory_2` |
| Hub / network node | `hub` |
| LAN / local network | `lan` |
| Network health | `network_check` |
| Device hub / IoT gateway | `device_hub` |
| Multi-workspace | `workspaces` |
| **Security / Auth** | |
| Locked / secure | `lock` |
| Unlocked | `lock_open` |
| Security posture | `security` |
| Shield / protection | `shield` |
| Key / auth token | `key` |
| API key / VPN | `vpn_key` |
| Verified user | `verified_user` |
| Biometric / identity | `fingerprint` |
| Privacy notice | `privacy_tip` |
| Admin config | `admin_panel_settings` |
| Security verified | `gpp_good` |
| **Development / Code** | |
| Code | `code` |
| Terminal | `terminal` |
| API | `api` |
| Integration | `integration_instructions` |
| Settings / config | `settings` |
| Build / construct | `build` |
| Launch / deploy | `rocket_launch` |
| Bug / issue tracking | `bug_report` |
| Dependency tree | `account_tree` |
| Dev mode | `developer_mode` |
| Plugin / extension | `extension` |
| Webhook / event push | `webhook` |
| **People / Teams** | |
| Individual / person | `person` |
| Add member / onboarding | `person_add` |
| Team / group | `group` |
| Larger org / all-hands | `groups` |
| Business / company | `business` |
| Corporate / HQ | `corporate_fare` |
| Manager / supervisor | `supervisor_account` |
| Account management | `manage_accounts` |
| Employee credentials | `badge` |
| Partnership / deal | `handshake` |
| **Actions / Flow** | |
| Next / forward | `arrow_forward` |
| Back / previous | `arrow_back` |
| Sync / refresh | `sync` |
| Run / execute | `play_circle` |
| Send / submit | `send` |
| Download | `download` |
| Upload | `upload` |
| Search | `search` |
| Bidirectional / two-way | `compare_arrows` |
| External link / new tab | `open_in_new` |
| Iterative / repeat | `loop` |
| Auto-renew / cycle | `autorenew` |
| Swap / exchange | `swap_horiz` |
| Add item | `add_circle` |
| Remove item | `remove_circle` |
| **Content / Documents** | |
| Document / file | `description` |
| Article / content | `article` |
| Edit / modify | `edit` |
| Summary / report | `summarize` |
| Folder | `folder` |
| Link / URL | `link` |
| Share | `share` |
| PDF export | `picture_as_pdf` |
| Dashboard view | `dashboard` |
| Documentation library | `library_books` |
| Contact / profile page | `contact_page` |
| Bullet list | `format_list_bulleted` |
| **AI / ML** | |
| AI / robot | `smart_toy` |
| AI reasoning | `psychology` |
| Model training | `model_training` |
| Insights | `insights` |
| AI magic / sparkle | `auto_awesome` |
| Auto-fix / optimize | `auto_fix_high` |
| **Finance / Business** | |
| Revenue / money | `attach_money` |
| Finance / banking | `account_balance` |
| Savings / efficiency | `savings` |
| Pricing / selling | `sell` |
| Invoice / billing | `receipt_long` |
| Payments | `payments` |
| Paid / settled | `paid` |
| Percentage | `percent` |
| **Time / Scheduling** | |
| Scheduled / time | `schedule` |
| Date / calendar | `calendar_today` |
| Date range | `date_range` |
| Event | `event` |
| Alarm / reminder | `alarm` |
| Timer / latency | `timer` |
| Waiting / processing | `hourglass_empty` |
| **Performance** | |
| Fast / performance | `speed` |
| Instant / real-time | `bolt` |
| Caching / cached result | `cached` |
| Tune / query config | `tune` |
| **Communication** | |
| Notifications / alerts | `notifications` |
| Email | `email` |
| Broadcast / announce | `campaign` |
| Chat / messaging | `chat` |
| Forum / discussion | `forum` |
| Support agent | `support_agent` |
| Feedback | `feedback` |
| **Global / Location** | |
| Global / worldwide | `public` |
| Language / locale | `language` |
| Location / region | `location_on` |
| Map | `map` |
| Explore / travel | `travel_explore` |
| **Data Operations** | |
| Filter / query | `filter_alt` |
| Transform / ETL | `transform` |
| Merge / join | `merge_type` |
| List / rows view | `view_list` |
| **Visualization / Layout** | |
| Layered architecture | `layers` |
| UI components / widgets | `widgets` |
| Card grid view | `view_module` |
| Split / side-by-side | `splitscreen` |
| Tabular data | `table_rows` |
| Grid layout | `grid_on` |
| Slides / carousel | `view_carousel` |
| Pipeline / stages | `linear_scale` |
| **Workflow / Process** | |
| Pending / in-progress | `pending_actions` |
| Approval process | `approval` |
| Comparison / diff | `compare` |
| Reorder / sort | `swap_vert` |
| Feature enabled | `toggle_on` |
| Feature disabled | `toggle_off` |
| Completed checklist | `playlist_add_check` |
| **Healthcare / Life Sciences** | |
| Health & safety | `health_and_safety` |
| Hospital / clinic | `local_hospital` |
| Medication / pharma | `medication` |
| Patient monitoring | `monitor_heart` |
| Biotech / lab | `biotech` |
| Vaccines | `vaccines` |
| **Retail / E-commerce** | |
| Storefront / retail | `storefront` |
| Shopping / cart | `shopping_cart` |
| Shipping / logistics | `local_shipping` |
| Inventory | `inventory` |
| **Financial Services** | |
| Credit card / payments | `credit_card` |
| Wallet / fintech | `account_balance_wallet` |
| Trading / markets | `candlestick_chart` |
| Currency exchange | `currency_exchange` |
| **Manufacturing / Industrial** | |
| Factory / plant | `factory` |
| Precision / robotics | `precision_manufacturing` |
| Engineering | `engineering` |
| Construction | `construction` |
| **Energy / Sustainability** | |
| Solar / renewable | `solar_power` |
| Eco / green | `eco` |
| Electricity / power | `electric_bolt` |
| Recycling / circular | `recycling` |
| Carbon / emissions | `co2` |
| **Transportation / Logistics** | |
| Automotive | `directions_car` |
| Aviation / travel | `flight` |
| Rail / transit | `train` |
| Warehouse | `warehouse` |
| **Education** | |
| School / university | `school` |
| Learning / textbook | `menu_book` |
| Research / science | `science` |
| **Government / Legal** | |
| Legal / regulation | `gavel` |
| Policy | `policy` |
| **Telecom / Connectivity** | |
| Cellular / telecom | `cell_tower` |
| WiFi / wireless | `wifi` |
| Router / network | `router` |
| **Media / Entertainment** | |
| Streaming / broadcast | `live_tv` |
| Podcast | `podcast` |
| Media / film | `movie` |
