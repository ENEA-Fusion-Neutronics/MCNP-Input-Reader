# MCNP Input Reader
> The package for reading mcnp input in a pythonic way

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mcnp-input-reader)](https://pypi.org/project/mcnp-input-reader/)
[![License](https://img.shields.io/pypi/l/mcnp-input-reader.svg)](https://github.com/ENEA-Fusion-Neutronics/MCNP-Input-Reader/blob/main/LICENSE)


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

