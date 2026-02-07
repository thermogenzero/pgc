# OpenFOAM -- Single HX Cell CFD

## Prerequisites

- [OpenFOAM v2312+](https://www.openfoam.com/) (ESI/OpenCFD version)
- `chtMultiRegionFoam` solver (included in standard distribution)

## What This Models

A single TEG heat exchanger cell (one 40x40mm TEG position) with:

- 9 parallel fin channels (3mm wide x 40mm tall x 40mm long)
- 10 copper fins (1mm thick, k = 385 W/m-K)
- Inlet/outlet manifold stubs
- TEG modeled as a thermal resistance boundary condition
- Conjugate heat transfer between fluid and solid (copper) regions

## Running

```bash
cd hx_cell
./Allrun
```

This will:
1. Generate the mesh (`blockMesh`)
2. Split regions (fluid + solid)
3. Set initial conditions
4. Run `chtMultiRegionFoam` for steady-state convergence

## Expected Results

- Temperature uniformity across TEG contact face (target: < 5 C variation)
- Pressure drop through fin channels
- Velocity distribution (expect laminar-to-turbulent transition)
- Heat transfer coefficient comparison with Dittus-Boelter correlation

## Post-Processing

```bash
paraFoam -case hx_cell
```

Or use `postProcess` for surface-averaged quantities:
```bash
postProcess -func 'patchAverage(name=tegFace, T)' -case hx_cell
```
