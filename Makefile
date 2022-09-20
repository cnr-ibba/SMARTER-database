.PHONY: clean clean_interim data lint requirements

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = [OPTIONAL] your-bucket-for-syncing-data (do not include 's3://')
PROFILE = default
PROJECT_NAME = SMARTER-database
PYTHON_INTERPRETER = python3
CURRENT_VERSION = $(shell awk -F " = " '/current_version/ {print $$2}' .bumpversion.cfg | head -n1)

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
initialize: requirements
	# import chip names
	$(PYTHON_INTERPRETER) src/data/import_snpchips.py --chip_file data/raw/chip_names.json

	## TODO: import manifest and SNPchimp for all assemblies

	## import data for Sheep

	### Oar_v3
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar3.1.csv.gz --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class sheep --manifest data/external/SHE/ILLUMINA/ovinesnpHD-genome-assembly-oar-v3-1.csv.gz \
		--chip_name IlluminaOvineHDSNP --version Oar_v3.1 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar3.1.csv.gz --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species_class sheep --manifest data/external/SHE/AFFYMETRIX/Axiom_BGovisNP_ovine_Annotation.r1.csv.gz \
		--chip_name AffymetrixAxiomBGovisNP --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species_class sheep --manifest data/external/SHE/AFFYMETRIX/Axiom_BGovis2_Annotation.r1.csv.gz \
		--chip_name AffymetrixAxiomBGovis2 --version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_consortium.py --species_class sheep --datafile data/external/SHE/CONSORTIUM/OvineSNP50_B.csv_v3.1_pos_20190513.csv.gz \
		--version Oar_v3.1
	$(PYTHON_INTERPRETER) src/data/import_consortium.py --species_class sheep --datafile data/external/SHE/CONSORTIUM/SheepHD_AgResearch_Cons_15041608_A.csv_v3.1_pos_20190513.csv.gz \
		--version Oar_v3.1

	### Oar_v4
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v4-0.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v4.0 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species_class sheep --manifest data/external/SHE/AFFYMETRIX/Axiom_Ovi_Can.na35.r3.a3.annot.csv.gz \
		--chip_name AffymetrixAxiomOviCan --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_consortium.py --species_class sheep --datafile data/external/SHE/CONSORTIUM/OvineSNP50_B.csvv4.0_pos_20190513.csv.gz \
		--version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_consortium.py --species_class sheep --datafile data/external/SHE/CONSORTIUM/SheepHD_AgResearch_Cons_15041608_A.csvv4.0_pos_20190513.csv.gz \
		--version Oar_v4.0

	## import data for goat
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class goat --manifest data/external/GOA/ILLUMINA/Goat_IGGC_65K_v2_15069617X365016_A2.csv.gz \
		--chip_name IlluminaGoatSNP50 --version ARS1 --sender IGGC
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class goat --snpchimp data/external/GOA/SNPCHIMP/SNPchimp_GOAT_SNP50_chi1.0.csv.gz --version CHI1.0

	## TODO: donwload data from EVA and EnsEMBL

## Make Dataset
data: requirements
	## upload datasets into database and unpack archives in interim folder
	## background data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes background data/raw/genotypes-bg.csv data/processed/genotypes-bg.json
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes background data/raw/phenotypes-bg.csv data/processed/phenotypes-bg.json

	## foreground data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes foreground data/raw/genotypes-fg.csv data/processed/genotypes-fg.json
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes foreground data/raw/phenotypes-fg.csv data/processed/phenotypes-fg.json

	## upload breeds into database and update aliases
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEXEL_UY --dataset TEXEL_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias 0 --dataset Frizarta54samples_ped_map_files.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Merino --code MER --alias MERINO_UY --dataset MERINO_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Corriedale --code CRR --alias CORRIEDALE_UY --dataset CORRIEDALE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Creole --code CRL --alias CRL --dataset CREOLE_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name "Mérinos d'Arles" --code ARL --alias MER --dataset="High density genotypes of French Sheep populations.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Sahel --code SAH --alias SHL --dataset ADAPTmap_genotypeTOP_20161201.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Bizet --code BIZ --alias BIZ --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name "Manech Tête Noire" --code MTN --alias MTN --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Solognote --code SOL --alias SOL --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name "Rouge du Roussillon" --code RDR --alias RDR --dataset SMARTER_OVIS_FRANCE.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias FRI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias FRI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Pelagonia --code PEL --alias PEL --dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Eghoria --code EGH --alias EGH --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Skopelos --code SKO --alias SKO --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Mytilini --code MYT --alias MYT --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Boutsko --code BOU --alias BOU --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Dalapäls --code DAL --alias DAL --dataset five_sweden_sheeps.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Fjällnäs --code FJA --alias FJA --dataset five_sweden_sheeps.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Gotland --code GOT --alias GOT --dataset five_sweden_sheeps.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Gute --code GUT --alias GUT --dataset five_sweden_sheeps.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Klövsjö --code KLO --alias KLO --dataset five_sweden_sheeps.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Fosses --code FSS --alias FOS --dataset SMARTER_CHFR.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Provencale --code PVC --alias PVC --dataset SMARTER_CHFR.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias 0 --dataset Frizarta_270.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Boutsko --code BOU --alias BOU --dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias FRI --dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Mytilini --code MYT --alias MYT --dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Chios --code CHI --alias CHI --dataset AUTH_OVN50KV2_CHI_FRZ.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias FRZ --dataset AUTH_OVN50KV2_CHI_FRZ.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Assaf --code ASF --alias Assaf --dataset SMARTER-500-ASSAF.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Assaf --code ASF --alias Assaf --dataset Castellana.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Castellana --code CAS --alias SMARTER --dataset Castellana.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Churra --code CHU --alias CHURRA --dataset Churra.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Assaf --code ASF --alias Assaf --dataset 20220326_resultados_SNP.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Castellana --code CAS --alias SMARTER --dataset 20220326_resultados_SNP.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Ojalada --code OJA --alias Smarter --dataset 20220428_Smarter_Ovine.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Ojalada --code OJA --alias Assaf --dataset 20220503_Ovine.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Creole --code CRL --alias CRL --dataset Placa_Junio_recommended.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Creole --code CRL --alias CRL --dataset OP829-924_INIA_Abril.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Creole --code CRL --alias CRL --dataset Placas1_4_genotyping.zip

	## load breeds into database relying on dataset
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset="High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --code_column Code --breed_column "Population Name"
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --code_column code --breed_column Breed \
		--fid_column Breed --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Goat --src_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_genotypeTOP_20161201/ADAPTmap_Breeds_20161201_fix.csv --breed_column Breed_fullname --code_column Breed_code
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset Nativesheep_Hu_metadata.zip --dst_dataset NativesheepBreeds_Hu.zip \
		--datafile nativesheeps_hu_fixed.xlsx --breed_column breed --code_column code --fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset isheep_50K_metadata.zip --dst_dataset isheep_50K.zip \
		--datafile isheep_50K_refined.xlsx --breed_column breed --code_column code --country_column country

	## create SHEEP samples from raw data files or from XLS (orders matter)
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
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Affymetrix_data_Plate_652_660.zip \
		--datafile Affymetrix_data_Plate_652_660/Uruguay_Corriedale_ID_GenotypedAnimals_fix.xlsx --code_all CRR --id_column "Sample Name" \
		--chip_name AffymetrixAxiomOviCan --country_all Uruguay --alias_column "Sample Filename"
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_OVIS_FRANCE \
		--dataset "SMARTER_OVIS_FRANCE.zip" --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_sheep.zip --dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --code_column breed_code --id_column sample_name \
		--chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SWE_sheep \
		--dataset "five_sweden_sheeps.zip" --chip_name IlluminaOvineHDSNP --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file friz \
		--dataset Frizarta_270.zip --coding ab --chip_name IlluminaOvineSNP50 --assembly OAR3 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_BOU_MYT_FRI.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_FRZ.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_FRZ.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaOvineSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Nativesheep_Hu_metadata.zip \
		--dst_dataset NativesheepBreeds_Hu.zip --datafile nativesheeps_hu_fixed.xlsx \
		--code_column fid --id_column original_id --chip_name IlluminaOvineSNP50 --country_column country
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file SMARTER-500-ASSAF --dataset SMARTER-500-ASSAF.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR3 --search_field probeset_id --create_samples \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "Castellana/20220131 Ovine" --dataset Castellana.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR3 --search_field probeset_id --create_samples \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Churra_metadata.zip \
		--dst_dataset Churra.zip --datafile metadata/Churra.xlsx \
		--code_column fid --id_column original_id --chip_name AffymetrixAxiomBGovisNP --country_column country
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220326_resultados_SNP/20220326_Ovine" --dataset 20220326_resultados_SNP.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR3 --search_field probeset_id --create_samples \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220428_Smarter_Ovine/20220428_Smarter_Ovine" --dataset 20220428_Smarter_Ovine.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR3 --search_field probeset_id --create_samples \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220503_Ovine/20220503_Ovine" --dataset 20220503_Ovine.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR3 --search_field probeset_id --create_samples \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset Placa_Junio_recommended.zip --datafile placa_junio_metadata.xlsx \
		--code_all CRL --id_column Lab_ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column id_column
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset OP829-924_INIA_Abril.zip --datafile inia_abril_metadata.xlsx \
		--code_all CRL --id_column Lab_ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column id_column
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset Placas1_4_genotyping.zip --datafile placas1_4_metadata.xlsx \
		--code_all CRL --id_column Lab_ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column id_column
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset isheep_50K_metadata.zip \
		--dst_dataset isheep_50K.zip --datafile isheep_50K_refined.xlsx \
		--code_column code --id_column sample_id --chip_name IlluminaOvineSNP50 --country_column country \
		--species_column species --sex_column sex

	## convert genotypes without creating samples in database (SHEEP)
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_652/Affymetrix_data_Plate_652 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_660/Affymetrix_data_Plate_660 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHI_FRI \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/Aristotle_University_OVN50KV02_20210720_FinalReport.txt \
		--snpfile AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/SNP_Map.txt --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHI_BOU_MYT_FRI/Aristotle_University_OVN50KV02_20211108 \
		--dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50K2_CHI_FRZ/Aristotle_University_OVN50KV02_20211124 \
		--dataset AUTH_OVN50KV2_CHI_FRZ.zip --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file NativesheepBreeds_Hu/NativeSheepGenotypes \
		--dataset NativesheepBreeds_Hu.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Churra/churra_fixed \
		--dataset Churra.zip --coding affymetrix --chip_name AffymetrixAxiomBGovis2 --assembly OAR3 \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placa_Junio_recommended.txt \
		--dataset Placa_Junio_recommended.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP829-924 INIA Abril.txt" \
		--dataset OP829-924_INIA_Abril.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placas1_4_genotyping.txt \
		--dataset Placas1_4_genotyping.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR3 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 50K-all \
		--dataset isheep_50K.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR3 \
		--search_field rs_id

	## create samples from custom files or genotypes for GOAT
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset ADAPTmap_phenotype_20161201.zip --dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --code_column Breed_code --id_column ADAPTmap_code \
		--chip_name IlluminaGoatSNP50 --country_column Sampling_Country --sex_column SEX --species_column Species
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --snpfile Swedish_Univ_Eriksson_GOAT53KV1_20200722/SNP_Map.txt \
		--report Swedish_Univ_Eriksson_GOAT53KV1_20200722/Swedish_Univ_Eriksson_GOAT53KV1_20200722_FinalReport.txt \
		--dataset Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip --breed_code LNR --chip_name IlluminaGoatSNP50 --assembly ARS1 --create_samples
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_goat.zip --dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile greece_foreground_goat/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaGoatSNP50 --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_CHFR \
		--dataset SMARTER_CHFR.zip --chip_name IlluminaGoatSNP50 --assembly ARS1 --create_samples

	## convert genotypes without creating samples in database (GOAT)
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile ADAPTmap_genotypeTOP_20161201/binary_fileset/ADAPTmap_genotypeTOP_20161201 \
		--dataset "ADAPTmap_genotypeTOP_20161201.zip" --chip_name IlluminaGoatSNP50 --assembly ARS1
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_GOAT53KV1_EGHORIA_SKOPELOS/Aristotle_University_GOAT53KV1_20200728_FinalReport.txt \
		--snpfile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/SNP_Map.txt --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--chip_name IlluminaGoatSNP50 --assembly ARS1

	## add additional metadata to samples
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset "High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --breed_column "Population Name" \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Link \
		--metadata_column POP_GROUP_CODE --metadata_column POP_GROUP_NAME
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --breed_column Breed \
		--latitude_column latitude --longitude_column longitude --metadata_column "Location/source" \
		--metadata_column Remark
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --id_column ADAPTmap_code \
		--latitude_column GPS_Latitude --longitude_column GPS_Longitude --metadata_column Sampling_info \
		--metadata_column DOB --metadata_column Notes --na_values NA
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_goat.zip \
		--dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile greece_foreground_goat/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding"
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding" --metadata_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_BOU_MYT_FRI.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding" --metadata_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset "Sweden_goat_metadata.zip" \
		--dst_dataset "Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip" \
		--datafile SMARTER-metadata-SLU.xlsx --sheet_name samples --id_column original_id \
		--latitude_column latitude --longitude_column longitude
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_FRZ.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_FRZ.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding" --metadata_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Nativesheep_Hu_metadata.zip \
		--dst_dataset NativesheepBreeds_Hu.zip --datafile nativesheeps_hu_fixed.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset Placa_Junio_recommended.zip --datafile placa_junio_metadata.xlsx --id_column Lab_ID \
		--metadata_column Site
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset OP829-924_INIA_Abril.zip --datafile inia_abril_metadata.xlsx --id_column Lab_ID \
		--metadata_column Site
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset 20220809_105_Creole_Samples_INIA_Uruguay.zip \
		--dst_dataset Placas1_4_genotyping.zip --datafile placas1_4_metadata.xlsx --id_column Lab_ID \
		--metadata_column Site
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset isheep_50K_metadata.zip \
		--dst_dataset isheep_50K.zip --datafile isheep_50K_refined.xlsx --id_column sample_id \
		--latitude_column latitude --longitude_column longitude --metadata_column biosample_id \
		--metadata_column biosample_url --metadata_column bioproject_id --metadata_column bioproject_url \
		--metadata_column location --metadata_column material --metadata_column technology \
		--metadata_column data_resource --metadata_column biosample_breed --metadata_column birth_location \
		--metadata_column geographic_location

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
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_goat.zip \
		--dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile greece_foreground_goat/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER-metadata-Uruguay_Metadata.zip \
		--dst_dataset CREOLE_INIA_UY.zip --sheet_name samples \
		--datafile SMARTER-metadata-Uruguay_Metadata.xlsx --id_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER-metadata-Uruguay_Metadata.zip \
		--dst_dataset CORRIEDALE_INIA_UY.zip --sheet_name samples \
		--datafile SMARTER-metadata-Uruguay_Metadata.xlsx --id_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER-metadata-Uruguay_Metadata.zip \
		--dst_dataset MERINO_INIA_UY.zip --sheet_name samples \
		--datafile SMARTER-metadata-Uruguay_Metadata.xlsx --id_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER-metadata-Uruguay_Metadata.zip \
		--dst_dataset TEXEL_INIA_UY.zip --sheet_name samples \
		--datafile SMARTER-metadata-Uruguay_Metadata.xlsx --id_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER-metadata-Uruguay_Metadata.zip \
		--dst_dataset Affymetrix_data_Plate_652_660.zip --sheet_name samples \
		--datafile SMARTER-metadata-Uruguay_Metadata.xlsx --alias_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_BOU_MYT_FRI.xlsx --id_column sample_name \
		--purpose_column Purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset "Sweden_goat_metadata.zip" \
		--dst_dataset "Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip" \
		--datafile SMARTER-metadata-SLU.xlsx --sheet_name samples --id_column original_id \
		--purpose_column purpose
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_FRZ.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_FRZ.xlsx --id_column sample_name \
		--purpose_column Purpose

	## merge SNPs into 1 file
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class sheep --assembly OAR3
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class goat --assembly ARS1

	## track database status
	$(PYTHON_INTERPRETER) src/data/update_db_status.py


## pack results to be shared via sFTP
publish:
	## SHEEP OAR3
	$(eval BASENAME=SMARTER-OA-OAR3-top-$(CURRENT_VERSION))
	cd ./data/processed/OAR3 && if [ -e $(BASENAME).zip ]; then rm $(BASENAME).zip; fi
	cd ./data/processed/OAR3 && zip -rvT $(BASENAME).zip $(BASENAME).bed $(BASENAME).bim $(BASENAME).fam $(BASENAME).hh $(BASENAME).log $(BASENAME).nosex
	cd ./data/processed/OAR3 && md5sum $(BASENAME).zip > $(BASENAME).md5
	find ./data/processed/OAR3 -type f \( -name "*.bed" -or -name "*.bim" -or -name "*.fam" -or -name "*.hh" -or -name "*.log" -or -name "*.nosex" \) -delete

	## GOAT ARS1
	$(eval BASENAME=SMARTER-CH-ARS1-top-$(CURRENT_VERSION))
	cd ./data/processed/ARS1 && if [ -e $(BASENAME).zip ]; then rm $(BASENAME).zip; fi
	cd ./data/processed/ARS1 && zip -rvT $(BASENAME).zip $(BASENAME).bed $(BASENAME).bim $(BASENAME).fam $(BASENAME).hh $(BASENAME).log $(BASENAME).nosex
	cd ./data/processed/ARS1 && md5sum $(BASENAME).zip > $(BASENAME).md5
	find ./data/processed/ARS1 -type f \( -name "*.bed" -or -name "*.bim" -or -name "*.fam" -or -name "*.hh" -or -name "*.log" -or -name "*.nosex" \) -delete

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete 2>/dev/null || /bin/true
	find . -type d -name "__pycache__" -delete 2>/dev/null || /bin/true

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
