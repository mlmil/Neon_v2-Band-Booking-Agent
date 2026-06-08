# GIMP Harness Spec

## Goal

Build a CLI-Anything harness for GIMP that lets Neon Blonde create and maintain venue template files without manual GUI work.

## Target Outcome

The harness should create a venue package that includes:
- a venue folder
- a `notes` document
- a 2048x2048 GIMP project file
- a 1200x600 GIMP project file option
- template text layers for the venue name, date, and time

## Project Assumptions

- Use CLI-Anything's GIMP harness pattern
- Prefer native GIMP batch/script support when available
- Use a stateful CLI with JSON mode and REPL
- Treat the `.xcf` file as the editable project output

## Required File Layout

```text
gimp/
└── agent-harness/
    ├── GIMP.md
    ├── setup.py
    └── cli_anything/
        └── gimp/
            ├── README.md
            ├── __init__.py
            ├── __main__.py
            ├── gimp_cli.py
            ├── core/
            ├── utils/
            └── tests/
```

## Required Commands

- `project new`
- `project open`
- `project save`
- `project info`
- `layer new`
- `layer add-from-file`
- `layer list`
- `draw text`
- `export render`
- `session undo`
- `session redo`

## Venue Template Behavior

When creating a venue template:
1. Create a 2048x2048 canvas.
2. Treat 2048x2048 as the default canvas.
3. Also support a 1200x600 canvas preset.
4. Add a background layer.
5. Add text layers in this order:
   - venue name
   - date in `SAT 5-10` style
   - time in `8-11` style
6. Save the project as the venue/date name.

## Validation

Verify:
- JSON output works
- REPL starts by default
- a project can be created and saved
- the venue template contains the expected layers
- subprocess invocation via `cli-anything-gimp` works
