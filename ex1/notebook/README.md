This directory contains the notebook and supporting files used to create the
tables and figures in the UBI paper.

`UBI-Working-Paper-Notebook.ipynb` contains the scripts used to create the results
`functions2.py` contains supporting functions used in the notebook
`benefitprograms.csv` contains a list of welfare and transfer programs that
would be cut in this specific reform and their associated costs
`cps_benefit.csv` contains benefit totals imputed using the open source C-TAM
model. C-TAM originally imputed values for each individual in the CPS, these
values were then aggregated to represent full tax-units

Note that `UBI-Working-Paper-Notebook.ipynb` will not run without
`puf_benefits.csv,` which we are unable included in this repository because it
relies on the 2009 IRS Statistics of Income Individual Public Use File, which
must be purchased from the IRS. If you have proof that you have purchased the 
2009 PUF, we will share `puf_benefits.csv` with you. 
