"""
We are in a **_source file_** (`splatlog/**/*.py`) docstring here; in particular
`doctor_genova/_linking.py`.

> 📝 NOTE
>
> The **Source** column is omitted because I can't figure out any way to display
> the source text... using HTML Entities like in the Markdown file version
> doesn't work because the Hash Prefix processor mangles them.

##### Hash Prefix #####

| Status |   Type   |                    Render                     |
| ------ | -------- | --------------------------------------------- |
| 🟡¹     | Local    | #DrGenPreprocessor                         |
| 🟡¹     | FQN      | #doctor_genova.preprocessor.DrGenPreprocessor |
| 🟢      | Stdlib   | #typing.IO                                    |
| 🟡¹     | Indirect | #doctor_genova.DrGenPreprocessor           |

> ¹ Succeeds on initial render, then fails on dynamic re-render.

##### `@pylink` Tag #####

| Status |   Type   |                         Render                         |
| ------ | -------- | ------------------------------------------------------ |
| 🟡²     | Local    | {@pylink DrGenPreprocessor}                            |
| 🟡²     | FQN      | {@pylink doctor_genova.preprocessor.DrGenPreprocessor} |
| 🟢      | Stdlib   | {@pylink typing.IO}                                    |
| 🟡²     | Indirect | {@pylink doctor_genova.DrGenPreprocessor}              |

> ² Succeeds on initial render, then fails on dynamic re-render.

##### Backtick Span #####

| Status |   Type   |                     Render                     |
| ------ | -------- | ---------------------------------------------- |
| 🟡³     | Local    | `DrGenPreprocessor`                         |
| 🟡³     | FQN      | `doctor_genova.preprocessor.DrGenPreprocessor` |
| 🟢      | Stdlib   | `typing.IO`                                    |
| 🟡³     | Indirect | `doctor_genova.DrGenPreprocessor`           |

> ³ Succeeds on initial render, then fails on dynamic re-render.

"""

from doctor_genova.preprocessor import DrGenPreprocessor
