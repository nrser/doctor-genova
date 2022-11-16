"""
We are in a **_source file_** (`splatlog/**/*.py`) docstring here; in particular
`doctor_genova/_linking.py`.

> 📝 NOTE
>
> The **Source** column is omitted because I can't figure out any way to display
> the source text... using HTML Entities like in the Markdown file version
> doesn't work because the Hash Prefix processor mangles them.

##### Hash Prefix #####

| Status |   Type   |                          Render                           |
| ------ | -------- | --------------------------------------------------------- |
| 🟡¹     | Local    | #BacktickPreprocessor                                     |
| 🟡¹     | FQN      | #doctor_genova.backtick_preprocessor.BacktickPreprocessor |
| 🟢      | Stdlib   | #typing.IO                                                |
| 🟡¹     | Indirect | #doctor_genova.BacktickPreprocessor                       |

> ¹ Succeeds on initial render, then fails on dynamic re-render.

##### `@pylink` Tag #####

| Status |   Type   |                               Render                               |
| ------ | -------- | ------------------------------------------------------------------ |
| 🔴²     | Local    | {@pylink BacktickPreprocessor}                                     |
| 🟡³     | FQN      | {@pylink doctor_genova.backtick_preprocessor.BacktickPreprocessor} |
| 🟢      | Stdlib   | {@pylink typing.IO}                                                |
| 🔴      | Indirect | {@pylink doctor_genova.BacktickPreprocessor}                       |

> ² Doesn't work because the source processor (which has access to the source
> node for contextual resolution) doesn't process `@pylink` tags.

> ³ Succeeds on initial render, then fails on dynamic re-render.

##### Backtick Span #####

| Status |   Type   |                           Render                           |
| ------ | -------- | ---------------------------------------------------------- |
| 🟡⁴     | Local    | `BacktickPreprocessor`                                     |
| 🟡⁴     | FQN      | `doctor_genova.backtick_preprocessor.BacktickPreprocessor` |
| 🟢      | Stdlib   | `typing.IO`                                                |
| 🟡⁴     | Indirect | `doctor_genova.BacktickPreprocessor`                       |

> ⁴ Succeeds on initial render, then fails on dynamic re-render.

"""
