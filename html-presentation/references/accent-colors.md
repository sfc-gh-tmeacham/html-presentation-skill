# Accent Color Selection

Pick an accent color based on the topic. If the user specifies a brand color, always use that instead.

| Topic Area | Suggested Accent | Hex |
|-----------|-----------------|-----|
| AI / Tech | Electric blue | `#3B82F6` |
| Business | Warm amber | `#F59E0B` |
| Design | Coral pink | `#F43F5E` |
| Finance | Emerald green | `#10B981` |
| Health | Soft teal | `#14B8A6` |
| Education | Royal purple | `#8B5CF6` |
| Marketing | Vibrant orange | `#F97316` |
| Snowflake | Snowflake blue | `#29B5E8` |
| General | Clean white accent | `#E5E5E5` |

The accent color is set as a CSS custom property and applied consistently to all highlights, icons, buttons, stat numbers, and emphasis throughout the deck:

```css
:root { --accent: #3B82F6; }
```
