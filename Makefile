.PHONY: clean data lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = [OPTIONAL] your-bucket-for-syncing-data (do not include 's3://')
PROFILE = default
PROJECT_NAME = SMARTER-database
PYTHON_INTERPRETER = python3

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
requirements: test_environment
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Initialize database by loading stuff
initialize: test_environment
	## upload datasets into database and unpack archives in interim folder
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes background data/raw/genotypes-bg.csv data/processed/genotypes-bg.json
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes background data/raw/phenotypes-bg.csv data/processed/phenotypes-bg.json

	## upload breeds into database and update aliases
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Texel --code TEX --alias TEXEL_UY --dataset TEXEL_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Frizarta --code FRZ --alias 0 --dataset Frizarta54samples_ped_map_files.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Merino --code MER --alias MERINO_UY --dataset MERINO_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Corriedale --code CRR --alias CORRIEDALE_UY --dataset CORRIEDALE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Creole --code CRL --alias CRL --dataset CREOLE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name "Mérinos d'Arles" --code ARL --alias MER --dataset="High density genotypes of French Sheep populations.zip"

	## load breeds into database relying on dataset
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species Sheep --dataset="High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --code_column Code --breed_column "Population Name"

	## TODO: import manifest and SNPchimp for all assemblies
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar3.1.csv.gz --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species sheep --manifest data/external/SHE/ILLUMINA/ovinesnpHD-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineHDSNP --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar3.1.csv.gz --version Oar_v3.1

	## TODO: donwload data from EVA and EnsEMBL

## Make Dataset
data: requirements
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file TEXEL_UY --dataset TEXEL_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Frizarta54samples_ped_map_files/Frizarta54samples \
		--dataset Frizarta54samples_ped_map_files.zip --coding forward
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file MERINO_UY_96_21_12_17_OV54k \
		--dataset MERINO_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file CORRIEDALE_UY_60_INIA_Ovine_14sep2010 \
		--dataset CORRIEDALE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport1.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport2.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile frenchsheep_HD \
		--dataset "High density genotypes of French Sheep populations.zip"

	## merge SNPs into 1 file
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species sheep --assembly OARV3

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8
lint:
	flake8 src

## Set up python interpreter environment
create_environment:
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, creating conda environment."
	conda env create -f environment.yml
	@echo ">>> New conda env created. Activate with:\nsource activate $(PROJECT_NAME)"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv virtualenvwrapper
	@echo ">>> Installing virtualenvwrapper if not already installed.\nMake sure the following lines are in shell startup file\n\
	export WORKON_HOME=$$HOME/.virtualenvs\nexport PROJECT_HOME=$$HOME/Devel\nsource /usr/local/bin/virtualenvwrapper.sh\n"
	@bash -c "source `which virtualenvwrapper.sh`;mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
endif

## Test python environment is setup correctly
test_environment:
	$(PYTHON_INTERPRETER) test_environment.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
