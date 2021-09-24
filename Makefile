.PHONY: clean clean_interim data lint requirements

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
	# import chip names
	$(PYTHON_INTERPRETER) src/data/import_snpchips.py --chip_file data/raw/chip_names.json

	## TODO: import manifest and SNPchimp for all assemblies
	## import data for Sheep
	## Oar_v3
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar3.1.csv.gz --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species sheep --manifest data/external/SHE/ILLUMINA/ovinesnpHD-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineHDSNP --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar3.1.csv.gz --version Oar_v3.1

	## Oar_v4
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v4-0.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v4.0 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species sheep --manifest data/external/SHE/AFFYMETRIX/Axiom_Ovi_Can.na35.r3.a3.annot.csv.gz \
		--chip_name AffymetrixAxiomOviCan --version Oar_v4.0

	## import data for goat
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species goat --manifest data/external/GOA/ILLUMINA/Goat_IGGC_65K_v2_15069617X365016_A2.csv.gz \
		--chip_name IlluminaGoatSNP50 --version ARS1 --sender IGGC
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species goat --snpchimp data/external/GOA/SNPCHIMP/SNPchimp_GOAT_SNP50_chi1.0.csv.gz --version CHI1.0

	## TODO: donwload data from EVA and EnsEMBL

## Make Dataset
data: requirements
	## upload datasets into database and unpack archives in interim folder
	## background data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes background data/raw/genotypes-bg.csv data/processed/genotypes-bg.json
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes background data/raw/phenotypes-bg.csv data/processed/phenotypes-bg.json

	## foreground data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes foreground data/raw/genotypes-fg.csv data/processed/genotypes-fg.json

	## upload breeds into database and update aliases
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Texel --code TEX --alias TEXEL_UY --dataset TEXEL_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Frizarta --code FRZ --alias 0 --dataset Frizarta54samples_ped_map_files.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Merino --code MER --alias MERINO_UY --dataset MERINO_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Corriedale --code CRR --alias CORRIEDALE_UY --dataset CORRIEDALE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Creole --code CRL --alias CRL --dataset CREOLE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name "Mérinos d'Arles" --code ARL --alias MER --dataset="High density genotypes of French Sheep populations.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species Goat --name Sahel --code SAH --alias SHL --dataset ADAPTmap_genotypeTOP_20161201.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Bizet --code BIZ --alias BIZ --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name "Manech Tête Noire" --code MTN --alias MTN --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Solognote --code SOL --alias SOL --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name "Rouge du Roussillon" --code RDR --alias RDR --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Frizarta --code FRZ --alias FRI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Frizarta --code FRZ --alias FRI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species sheep --name Pelagonia --code PEL --alias PEL --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species Goat --name Eghoria --code EGH --alias EGH --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species Goat --name Skopelos --code SKO --alias SKO --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip

	## load breeds into database relying on dataset
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species Sheep --dataset="High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --code_column Code --breed_column "Population Name"
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species Sheep --dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --code_column code --breed_column Breed \
		--fid_column Breed --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species Goat --dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_genotypeTOP_20161201/ADAPTmap_Breeds_20161201_fix.csv --breed_column Breed_fullname --code_column Breed_code

	## import data from plink (or report) files for SHEEP (and create samples if not exist)
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file TEXEL_UY --dataset TEXEL_INIA_UY.zip --chip_name IlluminaOvineSNP50 \
		--assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Frizarta54samples_ped_map_files/Frizarta54samples \
		--dataset Frizarta54samples_ped_map_files.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file MERINO_UY_96_21_12_17_OV54k \
		--dataset MERINO_INIA_UY.zip --chip_name IlluminaOvineSNP50 --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file CORRIEDALE_UY_60_INIA_Ovine_14sep2010 \
		--dataset CORRIEDALE_INIA_UY.zip --chip_name IlluminaOvineSNP50 --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport1.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport2.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile frenchsheep_HD \
		--dataset "High density genotypes of French Sheep populations.zip" --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file ovine_SNP50HapMap_data/SNP50_Breedv1/SNP50_Breedv1 \
		--dataset ovine_SNP50HapMap_data.zip --chip_name IlluminaOvineSNP50 --assembly OAR3 --create_samples

	## create samples from custom files for sheep (should be after others sample created or smarter IDS will be not consistent)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Affymetrix_data_Plate_652_660.zip --dst_dataset Affymetrix_data_Plate_652_660.zip \
		--datafile Affymetrix_data_Plate_652_660/Uruguay_Corriedale_ID_GenotypedAnimals_fix.xlsx --code_all CRR --id_column "Sample Name" \
		--chip_name AffymetrixAxiomOviCan --country_all Uruguay --alias_column "Sample Filename"
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_OVIS_FRANCE \
		--dataset "SMARTER_OVIS_FRANCE.zip" --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip --dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --code_column breed_code --id_column sample_name \
		--chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaOvineSNP50 --country_column Country

	## convert genotypes without creating samples in database (SHEEP)
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --file Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_652/Affymetrix_data_Plate_652 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --file Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_660/Affymetrix_data_Plate_660 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHI_FRI \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3

	## create samples from custom files or genotypes for GOAT
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset ADAPTmap_phenotype_20161201.zip --dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --code_column Breed_code --id_column ADAPTmap_code \
		--chip_name IlluminaGoatSNP50 --country_column Sampling_Country --sex_column SEX
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --snpfile Swedish_Univ_Eriksson_GOAT53KV1_20200722/SNP_Map.txt \
		--report Swedish_Univ_Eriksson_GOAT53KV1_20200722/Swedish_Univ_Eriksson_GOAT53KV1_20200722_FinalReport.txt \
		--dataset Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip --breed_code LNR --chip_name IlluminaGoatSNP50 --assembly ARS1 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip --dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaGoatSNP50 --country_column Country

	## convert genotypes without creating samples in database (GOAT)
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile ADAPTmap_genotypeTOP_20161201/binary_fileset/ADAPTmap_genotypeTOP_20161201 \
		--dataset "ADAPTmap_genotypeTOP_20161201.zip" --chip_name IlluminaGoatSNP50 --assembly ARS1
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_GOAT53KV1_EGHORIA_SKOPELOS/Aristotle_University_GOAT53KV1_20200728_FinalReport.txt \
	 	--snpfile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/SNP_Map.txt --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--chip_name IlluminaGoatSNP50 --assembly ARS1

	## add additional metadata to samples
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset "High density genotypes of French Sheep populations.zip" \
		--dst_dataset "High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --breed_column "Population Name" \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Link \
		--metadata_column POP_GROUP_CODE --metadata_column POP_GROUP_NAME
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset=ovine_SNP50HapMap_data.zip \
		--dst_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --breed_column Breed \
		--latitude_column latitude --longitude_column longitude --metadata_column "Location/source" \
		--metadata_column Remark
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --id_column ADAPTmap_code \
		--latitude_column GPS_Latitude --longitude_column GPS_Longitude --metadata_column Sampling_info \
		--metadata_column DOB --metadata_column Notes --na_values NA
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"

	## add phenotypes to samples
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/adaptmap_phenotypes_by_breed_fix.xlsx --breed_column "Breed name" \
		--sheet_name "Purpose" --purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/adaptmap_phenotypes_by_breed_fix.xlsx --breed_column "Breed name" \
		--sheet_name "Coat color" --additional_column "Coat color"
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/adaptmap_phenotypes_by_breed_fix.xlsx --breed_column "Breed name" \
		--sheet_name "Köppen" --additional_column "Köppen group"
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --id_column ADAPTmap_code \
		--chest_girth_column ChestGirth --height_column Height --length_column Length \
		--additional_column FAMACHA --additional_column WidthOfPinBones
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx --id_column sample_name \
		--purpose_column Purpose

	## merge SNPs into 1 file
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species sheep --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species goat --assembly ARS1

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Delete data interim contents
clean_interim:
	find ./data/interim/ -not -path "./data/interim/.gitkeep" -type f -delete
	find ./data/interim/ -not -path "./data/interim/" -type d -delete

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

## Test code
test:
	coverage run --source src -m py.test
	coverage html

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
