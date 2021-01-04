# MCNP Input Reader
> The python package for reading mcnp input in a python way

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mcnp-input-reader)
MCNP Input Reader is a python package developed in ENEA to help the modifications and the check integrity 
of large mcnp input files.

## Install

```shell
pip install mcnp-input-reader
```

## Usage

```python
import mcnp_input_reader as mir

mcnp_input = mir.read_file('input.i') 
mcnp_input.cells # return the table of cells
mcnp_input.cells.filter(lambda cell: cell.mat_id == 2) # return the cells using material M2
```
## TODO

A lot of things...

## Example

Example taken from [here](https://www.utoledo.edu/med/depts/radther/pdf/MCNP5%20practical%20examples%20lecture%207%20companion.pdf) 

