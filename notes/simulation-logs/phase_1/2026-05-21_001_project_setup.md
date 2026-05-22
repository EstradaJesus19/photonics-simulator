# 2026-05-22 — Project Setup

## 1. Goal

The goal of this session was to set up the initial structure of the Photonics Simulator project.

This includes creating the local project folder, preparing the Python environment, organizing the documentation folders, and defining the first phase of the project.

---

## 2. Context

This work belongs to Phase 1 of the project.

Phase 1 focuses on building a simple 2D wave simulation using the scalar wave equation.

The long-term goal is to build toward a more complete photonics simulation toolkit, eventually including material regions, boundary conditions, and electromagnetic FDTD methods.

---

## 3. Changes made

The following project structure was planned or created:

```text
photonics-simulator/
│
├── simulations/
│   └── wave2d_basic.py
│
├── notes/
│   ├── physics/
│   │   └── 01_wave_equation.md
│   │
│   ├── mathematics/
│   │   └── 01_finite_differences.md
│   │
│   ├── simulation_logs/
│   │   ├── README.md
│   │   └── phase_1/
│   │       └── 2026-05-22_001_project_setup.md
│   │
│   └── next_steps/
│       └── phase_1_roadmap.md
│
├── requirements.txt
├── README.md
└── .gitignore
```

The notes folder was divided into separate categories:

- `physics/`
- `mathematics/`
- `simulation_logs/`
- `next_steps/`

This decision was made to keep the documentation organized as the project grows.

---

## 4. Environment setup

The project uses Python as the main programming language.

The initial required Python packages are:

```text
numpy
matplotlib
```

The planned environment setup commands are:

```bash
python -m venv .venv
```

Activate the environment.

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install numpy matplotlib
```

Save dependencies:

```bash
pip freeze > requirements.txt
```

---

## 5. Results observed

At this stage, the project structure was defined.

The main result is that the project now has a clear organization separating:

- source code,
- physics notes,
- mathematics notes,
- simulation logs,
- and roadmap files.

This structure should make the repository easier to understand and maintain.

---

## 6. Interpretation

The project is being treated as a technical simulation project, not only as a collection of Python scripts.

The documentation structure is important because it records the reasoning behind the implementation.

This is especially useful for a portfolio project, because it shows not only the final result but also the development process.

---

## 7. Problems or limitations

At this stage, the simulation itself may not yet be fully implemented or tested.

The project also does not yet include:

- automated tests,
- physical units,
- advanced boundary conditions,
- material regions,
- or electromagnetic field components.

These limitations are expected because this is the initial setup stage.

---

## 8. Decisions made

The following decisions were made:

1. Use Python for the first implementation.
2. Use NumPy for numerical arrays.
3. Use Matplotlib for visualization.
4. Start with the scalar 2D wave equation instead of full Maxwell equations.
5. Organize notes into topic-specific folders.
6. Use simulation logs as a technical lab notebook.
7. Add Git/GitHub version control after the initial local structure is working.

---

## 9. Next steps

The next steps are:

1. Create the first simulation script.
2. Implement the 2D scalar wave equation.
3. Use a Gaussian pulse as the initial condition.
4. Animate the field evolution.
5. Observe the wave propagation.
6. Record results in a second simulation log.
