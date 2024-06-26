.PHONY: clean clean_interim data lint requirements assemblies

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = [OPTIONAL] your-bucket-for-syncing-data (do not include 's3://')
PROFILE = default
PROJECT_NAME = SMARTER-database
PYTHON_INTERPRETER = python3
CURRENT_VERSION = $(shell awk -F " = " '/current_version/ {print $$2}' .bumpversion.cfg | head -n1)
SHEEP_ASSEMBLIES := OAR3 OAR4
GOAT_ASSEMBLIES := ARS1 CHI1

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
	poetry install

## Initialize database by loading stuff
initialize: requirements
	# import chip names
	$(PYTHON_INTERPRETER) src/data/import_snpchips.py --chip_file data/raw/chip_names.json

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
	$(PYTHON_INTERPRETER) src/data/import_isgc.py --datafile data/external/SHE/CONSORTIUM/OvineSNP50_B.csv_v3.1_pos_20190513.csv.gz \
		--version Oar_v3.1 --date 2019-07-02
	$(PYTHON_INTERPRETER) src/data/import_isgc.py --datafile data/external/SHE/CONSORTIUM/SheepHD_AgResearch_Cons_15041608_A.csv_v3.1_pos_20190513.csv.gz \
		--version Oar_v3.1 --date 2019-07-02

	### Oar_v4
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class sheep --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v4-0.csv.gz \
		--chip_name IlluminaOvineSNP50 --version Oar_v4.0 --sender AGR_BS
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class sheep --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNPHDv1_oar4.0.csv.gz --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species_class sheep --manifest data/external/SHE/AFFYMETRIX/Axiom_Ovi_Can.na35.r3.a3.annot.csv.gz \
		--chip_name AffymetrixAxiomOviCan --version Oar_v4.0
	$(PYTHON_INTERPRETER) src/data/import_isgc.py --datafile data/external/SHE/CONSORTIUM/OvineSNP50_B.csvv4.0_pos_20190513.csv.gz \
		--version Oar_v4.0 --date 2019-07-02
	$(PYTHON_INTERPRETER) src/data/import_isgc.py --datafile data/external/SHE/CONSORTIUM/SheepHD_AgResearch_Cons_15041608_A.csvv4.0_pos_20190513.csv.gz \
		--version Oar_v4.0 --date 2019-07-02
	$(PYTHON_INTERPRETER) src/data/import_dbsnp.py --input_dir data/external/SHE/dbSNP --species_class Sheep --sender AGR_BS --version Oar_v4.0

	## import data for goat
	$(PYTHON_INTERPRETER) src/data/import_manifest.py --species_class goat --manifest data/external/GOA/ILLUMINA/Goat_IGGC_65K_v2_15069617X365016_A2.csv.gz \
		--chip_name IlluminaGoatSNP50 --version ARS1 --sender IGGC
	$(PYTHON_INTERPRETER) src/data/import_snpchimp.py --species_class goat --snpchimp data/external/GOA/SNPCHIMP/SNPchimp_GOAT_SNP50_chi1.0.csv.gz --version CHI1.0
	$(PYTHON_INTERPRETER) src/data/import_iggc.py --datafile data/external/GOA/CONSORTIUM/capri4dbsnp-base-CHI-ARS-OAR-UMD.csv.gz \
		--version ARS1 --date "06 Mar 2018" --chrom_column ars1_chr --pos_column ars1_pos --strand_column ars1_strand
	$(PYTHON_INTERPRETER) src/data/import_iggc.py --datafile data/external/GOA/CONSORTIUM/capri4dbsnp-base-CHI-ARS-OAR-UMD.csv.gz \
		--version CHI1.0 --date "06 Mar 2018" --chrom_column chi_1_0_chr --pos_column chi_1_0_pos --strand_column chi_1_0_strand
	$(PYTHON_INTERPRETER) src/data/import_dbsnp.py --input_dir data/external/GOA/dbSNP --species_class Goat --sender IGGC --version CHI1.0
	$(PYTHON_INTERPRETER) src/data/import_affymetrix.py --species_class goat --manifest data/external/GOA/AFFYMETRIX/Axiom_Goat_v2.r1.a1.annot.csv.gz \
		--chip_name AffymetrixAxiomGoatv2 --version ARS1

	## TODO: donwload data from EVA and EnsEMBL

## Make Dataset
data: requirements
	## upload datasets into database and unpack archives in interim folder
	## background data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes background data/raw/genotypes-bg.csv
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes background data/raw/phenotypes-bg.csv

	## foreground data
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types genotypes foreground data/raw/genotypes-fg.csv
	$(PYTHON_INTERPRETER) src/data/import_datasets.py --types phenotypes foreground data/raw/phenotypes-fg.csv

	## upload breeds into database and update aliases
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEXEL_UY --dataset TEXEL_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Frizarta --code FRZ --alias 0 --dataset Frizarta54samples_ped_map_files.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Merino --code MER --alias MERINO_UY --dataset MERINO_INIA_UY.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Merino --code MER --alias MER --dataset MERINO_INIA_UY.zip
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
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset Inia_junio_2021_Texel_46_20210409_SMARTER.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset "OP635-818 genotyping_soloTexel_20211110_SMARTER.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Corriedale --code CRR --alias CRR --dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset "OP829-924 INIA Abril_20220301_Texel_SMARTER.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Texel --code TEX --alias TEX --dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class sheep --name Corriedale --code CRR --alias CRR --dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip"
	$(PYTHON_INTERPRETER) src/data/add_breed.py --species_class Goat --name Guisandesa --code GUI --alias Goat --dataset Guisandesa.zip

	## load breeds into database relying on dataset
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset="High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --code_column Code --breed_column "Population Name" --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --code_column code --breed_column Breed \
		--fid_column Breed --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Goat --src_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_genotypeTOP_20161201/ADAPTmap_Breeds_20161201_fix.csv --breed_column Breed_fullname --code_column Breed_code
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset Nativesheep_Hu_metadata.zip --dst_dataset NativesheepBreeds_Hu.zip \
		--datafile nativesheeps_hu_fixed.xlsx --breed_column breed --code_column code --fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset isheep_50K_metadata.zip --dst_dataset isheep_50K.zip \
		--datafile isheep_50K_refined.xlsx --breed_column breed --code_column code --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset isheep_600K_metadata.zip --dst_dataset isheep_600K.zip \
		--datafile isheep_600K_refined.xlsx --breed_column breed --code_column code --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset isheep_WGS_metadata.zip --dst_dataset isheep_WGS.zip \
		--datafile isheep_WGS_refined.xlsx --breed_column breed --code_column code --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/SNP50_Breedv2.xlsx --code_column code --breed_column breed \
		--fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset Welsh_sheep_genotyping.zip \
		--datafile welsh-metadata.xlsx --code_column code --breed_column breed \
		--fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_muflon_metadata.xlsx --code_column code --breed_column Breed \
		--fid_column fid --country_column country_x
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_sheep_metadata.xlsx --code_column code --breed_column breed_x \
		--fid_column code --country_column country_x
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset Ciani_2020.zip \
		--datafile 8947346/ciani_2020_metadata_fix.xlsx --code_column code --breed_column breed \
		--fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset northwest_africa_sheep.zip \
		--datafile northwest_africa_sheep/belabdi_2019_metadata.xlsx --code_column code --breed_column breed \
		--fid_column fid --country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Sheep --src_dataset gaouar_algerian_sheeps.zip \
		--datafile AlgerianSheep/gaouar_2017_metadata_fix.xlsx --code_column code --breed_column Name \
		--fid_column Fid --country_column Country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Goat --src_dataset burren_et_al_2016.zip \
		--datafile doi_10.5061_dryad.q1cv6__v1/burren_samples_fix.xlsx --breed_column breed --code_column code \
		--country_column country
	$(PYTHON_INTERPRETER) src/data/import_breeds.py --species_class Goat --src_dataset cortellari_et_al_2021.zip \
		--datafile s41598-021-89900-2/cortellari_samples_fix.xlsx --breed_column breed --code_column code \
		--fid_column fid

	## create SHEEP samples from raw data files or from XLS (orders matter)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file TEXEL_UY \
		--dataset TEXEL_INIA_UY.zip --chip_name IlluminaOvineSNP50 \
		--assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Frizarta54samples_ped_map_files/Frizarta54samples \
		--dataset Frizarta54samples_ped_map_files.zip --src_coding forward --chip_name IlluminaOvineSNP50 \
		--assembly $(ASSEMBLY) --create_samples;)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset MERINO_INIA_UY.zip \
		--datafile MERINO_UY_96_21_12_17_OV54k_samples.xlsx --code_column code --id_column iid \
		--chip_name IlluminaOvineSNP50 --country_column country
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file CORRIEDALE_UY_60_INIA_Ovine_14sep2010 \
		--dataset CORRIEDALE_INIA_UY.zip --chip_name IlluminaOvineSNP50 \
		--assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport1.txt \
		--snpfile OvineHDSNPList.txt --dataset CREOLE_INIA_UY.zip --breed_code CRL \
		--chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport2.txt \
		--snpfile OvineHDSNPList.txt --dataset CREOLE_INIA_UY.zip --breed_code CRL \
		--chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile frenchsheep_HD \
		--dataset "High density genotypes of French Sheep populations.zip" \
		--chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file ovine_SNP50HapMap_data/SNP50_Breedv1/SNP50_Breedv1 \
		--dataset ovine_SNP50HapMap_data.zip --chip_name IlluminaOvineSNP50 \
		--assembly $(ASSEMBLY) --create_samples;)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Affymetrix_data_Plate_652_660.zip \
		--datafile Affymetrix_data_Plate_652_660/Uruguay_Corriedale_ID_GenotypedAnimals_fix.xlsx --code_all CRR --id_column "Sample Name" \
		--chip_name AffymetrixAxiomOviCan --country_all Uruguay --alias_column "Sample Filename"
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_OVIS_FRANCE \
		--dataset "SMARTER_OVIS_FRANCE.zip" --chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --create_samples;)
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
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SWE_sheep \
		--dataset "five_sweden_sheeps.zip" --chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --create_samples;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file friz \
		--dataset Frizarta_270.zip --src_coding ab --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --create_samples;)
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
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file SMARTER-500-ASSAF \
		--dataset SMARTER-500-ASSAF.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly $(ASSEMBLY) \
		--search_field probeset_id --create_samples --src_version Oar_v3.1 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "Castellana/20220131 Ovine" \
		--dataset Castellana.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly $(ASSEMBLY) \
		--search_field probeset_id --create_samples --src_version Oar_v3.1 --src_imported_from affymetrix;)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Churra_metadata.zip \
		--dst_dataset Churra.zip --datafile metadata/Churra.xlsx \
		--code_column fid --id_column original_id --chip_name AffymetrixAxiomBGovisNP --country_column country
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220326_resultados_SNP/20220326_Ovine" \
		--dataset 20220326_resultados_SNP.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly $(ASSEMBLY) \
		--search_field probeset_id --create_samples --src_version Oar_v3.1 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220428_Smarter_Ovine/20220428_Smarter_Ovine" \
		--dataset 20220428_Smarter_Ovine.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly $(ASSEMBLY) \
		--search_field probeset_id --create_samples --src_version Oar_v3.1 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220503_Ovine/20220503_Ovine" \
		--dataset 20220503_Ovine.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly $(ASSEMBLY) \
		--search_field probeset_id --create_samples --src_version Oar_v3.1 --src_imported_from affymetrix;)
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
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset isheep_600K_metadata.zip \
		--dst_dataset isheep_600K.zip --datafile isheep_600K_refined.xlsx \
		--code_column code --id_column sample_id --chip_name IlluminaOvineHDSNP	--country_column country \
		--species_column species --sex_column sex --alias_column alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset isheep_WGS_metadata.zip \
		--dst_dataset isheep_WGS.zip --datafile isheep_WGS_refined.xlsx \
		--code_column code --id_column sample_id --chip_name WholeGenomeSequencing --country_column country \
		--species_column species --sex_column sex --alias_column alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset ovine_SNP50HapMap_data.zip \
		--dst_dataset ovine_SNP50HapMap_data.zip --datafile ovine_SNP50HapMap_data/SNP50_Breedv2.xlsx \
		--code_column fid --id_column original_id --chip_name IlluminaOvineSNP50 --country_column country \
		--species_all "Ovis aries"
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset Inia_junio_2021_Texel_46_20210409_SMARTER.zip --datafile 20210409_Genexa_fix.xlsx \
		--code_all TEX --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP635-818 genotyping_soloTexel_20211110_SMARTER.zip" --datafile 20211110_Genexa_fix.xlsx \
		--code_all TEX --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip --datafile 20210824_Genexa_fix.xlsx \
		--code_column Code --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP829-924 INIA Abril_20220301_Texel_SMARTER.zip" --datafile 20220301_Genexa_fix.xlsx \
		--code_all TEX --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.zip" --datafile 20220323_Genexa_fix.xlsx \
		--code_all TEX --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip" --datafile 20220810_Genexa_fix.xlsx \
		--code_column Code --id_column ID --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
		--sex_column Sex --alias_column alias --skip_missing_alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Welsh_sheep_genotyping.zip \
		--datafile welsh-metadata.xlsx --code_column fid --id_column original_id --chip_name IlluminaOvineSNP50 \
		--country_column country
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_muflon_metadata.xlsx --code_column fid --id_column original_id \
		--chip_name IlluminaOvineSNP50 --country_column country_x --species_column Species --alias_column alias \
		--sex_column sex
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_sheep_metadata.xlsx --code_column code --id_column original_id \
		--chip_name IlluminaOvineSNP50 --country_column country_x --sex_column sex
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Ciani_2020.zip \
		--datafile 8947346/ciani_2020_metadata_fix.xlsx --code_column fid --id_column original_id \
		--chip_name IlluminaOvineSNP50 --country_column country --species_column species
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset northwest_africa_sheep.zip \
		--datafile northwest_africa_sheep/belabdi_2019_metadata.xlsx --code_column fid --id_column original_id \
		--chip_name IlluminaOvineSNP50 --country_column country --sex_column sexe
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset gaouar_algerian_sheeps.zip \
		--datafile AlgerianSheep/gaouar_2017_metadata_fix.xlsx --code_column Fid --id_column original_id \
		--chip_name IlluminaOvineSNP50 --country_column Country

	## convert genotypes without creating samples in database (SHEEP)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES),  $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file MERINO_UY_96_21_12_17_OV54k \
		--dataset MERINO_INIA_UY.zip --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_652/Affymetrix_data_Plate_652 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_660/Affymetrix_data_Plate_660 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHI_FRI \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip --src_coding forward --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip --src_coding forward --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/Aristotle_University_OVN50KV02_20210720_FinalReport.txt \
		--snpfile AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/SNP_Map.txt --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHI_BOU_MYT_FRI/Aristotle_University_OVN50KV02_20211108 \
		--dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50K2_CHI_FRZ/Aristotle_University_OVN50KV02_20211124 \
		--dataset AUTH_OVN50KV2_CHI_FRZ.zip --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file NativesheepBreeds_Hu/NativeSheepGenotypes \
		--dataset NativesheepBreeds_Hu.zip --src_coding forward --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Churra/churra_fixed \
		--dataset Churra.zip --src_coding affymetrix --chip_name AffymetrixAxiomBGovis2 --assembly $(ASSEMBLY) \
		--src_version Oar_v3.1 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placa_Junio_recommended.txt \
		--dataset Placa_Junio_recommended.zip --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP829-924 INIA Abril.txt" \
		--dataset OP829-924_INIA_Abril.zip --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placas1_4_genotyping.txt \
		--dataset Placas1_4_genotyping.zip --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 50K-all \
		--dataset isheep_50K.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) \
		--search_field rs_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 600K-all \
		--dataset isheep_600K.zip --src_coding top --chip_name IlluminaOvineHDSNP --assembly $(ASSEMBLY) --sample_field alias \
		--search_field rs_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile WGS-all.smarter \
		--dataset isheep_WGS.zip --src_coding forward --chip_name WholeGenomeSequencing --assembly $(ASSEMBLY) --sample_field alias \
		--search_by_positions --src_version Oar_v4.0 --src_imported_from "SNPchiMp v.3" --ignore_coding_errors;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file ovine_SNP50HapMap_data/SNP50_Breedv2/SNP50_Breedv2 \
		--dataset ovine_SNP50HapMap_data.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Inia_junio_2021_Texel_46_20210409_SMARTER.txt \
		--dataset Inia_junio_2021_Texel_46_20210409_SMARTER.zip --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 38;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP635-818 genotyping_soloTexel_20211110_SMARTER.txt" \
		--dataset "OP635-818 genotyping_soloTexel_20211110_SMARTER.zip" --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 59;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.txt \
		--dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 332;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP829-924 INIA Abril_20220301_Texel_SMARTER.txt" \
		--dataset "OP829-924 INIA Abril_20220301_Texel_SMARTER.zip" --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 43;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.txt" \
		--dataset "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.zip" --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 25;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.txt" \
		--dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip" --src_coding ab --chip_name AffymetrixAxiomOviCan --assembly $(ASSEMBLY) \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 35 --skip_coordinate_check;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "genotyping data/WelshSheepBreeds2015" \
		--dataset Welsh_sheep_genotyping.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 41598_2017_7382_MOESM2_ESM/Barbato_2016 \
		--dataset 41598_2017_7382_MOESM2_ESM.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 8947346/OaSNP1477x44430-1807 \
		--dataset Ciani_2020.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file northwest_africa_sheep/AlgerianSheepSidaounHamra \
		--dataset northwest_africa_sheep.zip --src_coding top --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id;)
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file AlgerianSheep/AlgerianSheep \
		--dataset gaouar_algerian_sheeps.zip --src_coding illumina --chip_name IlluminaOvineSNP50 --assembly $(ASSEMBLY) --sample_field original_id \
		--src_version Oar_v4.0 --src_imported_from manifest;)

	## create samples from custom files or genotypes for GOAT
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset ADAPTmap_phenotype_20161201.zip --dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --code_column Breed_code --id_column ADAPTmap_code \
		--chip_name IlluminaGoatSNP50 --country_column Sampling_Country --sex_column SEX --species_column Species
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_illumina.py --snpfile Swedish_Univ_Eriksson_GOAT53KV1_20200722/SNP_Map.txt \
		--report Swedish_Univ_Eriksson_GOAT53KV1_20200722/Swedish_Univ_Eriksson_GOAT53KV1_20200722_FinalReport.txt \
		--dataset Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip --breed_code LNR --chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY) --create_samples;)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset greece_foreground_goat.zip --dst_dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--datafile greece_foreground_goat/AUTH_GOAT53KV1_EGHORIA_SKOPELOS.xlsx \
		--code_column breed_code --id_column sample_name --chip_name IlluminaGoatSNP50 --country_column Country
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_CHFR \
		--dataset SMARTER_CHFR.zip --chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY) --create_samples;)
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset burren_et_al_2016.zip \
		--datafile doi_10.5061_dryad.q1cv6__v1/burren_samples_fix.xlsx --code_column code --id_column original_id \
		--chip_name IlluminaGoatSNP50 --country_all Switzerland --species_all Goat --alias_column alias
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset cortellari_et_al_2021.zip \
		--datafile s41598-021-89900-2/cortellari_samples_fix.xlsx --code_column fid --id_column original_id \
		--chip_name IlluminaGoatSNP50 --country_all Italy --species_all Goat
	$(PYTHON_INTERPRETER) src/data/import_samples.py --src_dataset Guisandesa.zip \
		--datafile Guisandesa/Guisandesa.xlsx --code_all GUI --id_column original_id \
		--chip_name AffymetrixAxiomGoatv2 --country_all Spain --species_all Goat

	## convert genotypes without creating samples in database (GOAT)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile ADAPTmap_genotypeTOP_20161201/binary_fileset/ADAPTmap_genotypeTOP_20161201 \
		--dataset "ADAPTmap_genotypeTOP_20161201.zip" --chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_GOAT53KV1_EGHORIA_SKOPELOS/Aristotle_University_GOAT53KV1_20200728_FinalReport.txt \
		--snpfile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/SNP_Map.txt --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file doi_10.5061_dryad.q1cv6__v1/goat_data2_dryad_fix \
		--dataset burren_et_al_2016.zip --chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY) --sample_field alias;)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile s41598-021-89900-2/Cortellari2021 \
		--dataset cortellari_et_al_2021.zip --chip_name IlluminaGoatSNP50 --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "Guisandesa/Guisandesa Goat" \
		--dataset Guisandesa.zip --src_coding affymetrix --chip_name AffymetrixAxiomGoatv2 --assembly $(ASSEMBLY) \
		--search_field probeset_id --src_version ARS1 --src_imported_from affymetrix;)

	## add additional metadata to samples
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset "High density genotypes of French Sheep populations.zip" \
		--datafile Populations_infos_fix.xlsx --breed_column "Population Name" \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Link \
		--metadata_column POP_GROUP_CODE --metadata_column POP_GROUP_NAME --species_column Species
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset=ovine_SNP50HapMap_data.zip \
		--datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx --breed_column Breed \
		--latitude_column latitude --longitude_column longitude --metadata_column "Location/source" \
		--metadata_column Remark
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset ADAPTmap_phenotype_20161201.zip \
		--dst_dataset ADAPTmap_genotypeTOP_20161201.zip \
		--datafile ADAPTmap_phenotype_20161201/ADAPTmap_InfoSample_20161201_fix.xlsx --id_column ADAPTmap_code \
		--latitude_column GPS_Latitude --longitude_column GPS_Longitude --metadata_column Sampling_info \
		--metadata_column DOB --notes_column Notes --na_values NA
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
		--metadata_column "Farm Coding" --notes_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_BOU_MYT_FRI.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding" --notes_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset "Sweden_goat_metadata.zip" \
		--dst_dataset "Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip" \
		--datafile SMARTER-metadata-SLU.xlsx --sheet_name samples --id_column original_id \
		--latitude_column latitude --longitude_column longitude
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset greece_foreground_sheep.zip \
		--dst_dataset AUTH_OVN50KV2_CHI_FRZ.zip \
		--datafile greece_foreground_sheep/AUTH_OVN50KV2_CHI_FRZ.xlsx --id_column sample_name \
		--latitude_column Latitude --longitude_column Longitude --metadata_column Region \
		--metadata_column "Farm Coding" --notes_column Note
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
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset isheep_600K_metadata.zip \
		--dst_dataset isheep_600K.zip --datafile isheep_600K_refined.xlsx --id_column sample_id \
		--latitude_column latitude --longitude_column longitude --metadata_column biosample_id \
		--metadata_column biosample_url --metadata_column bioproject_id --metadata_column bioproject_url \
		--metadata_column location --metadata_column material --metadata_column technology \
		--metadata_column data_resource --metadata_column biosample_breed --metadata_column breed_history \
		--metadata_column geographic_location
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset isheep_WGS_metadata.zip \
		--dst_dataset isheep_WGS.zip --datafile isheep_WGS_refined.xlsx --alias_column alias \
		--latitude_column latitude --longitude_column longitude --metadata_column biosample_id \
		--metadata_column biosample_url --metadata_column bioproject_id --metadata_column bioproject_url \
		--metadata_column location --metadata_column material --metadata_column technology \
		--metadata_column data_resource --metadata_column geographic_location --metadata_column ecotype \
		--metadata_column storage_conditions --metadata_column ena_url --metadata_column insdc_center_name \
		--metadata_column sra_accession --metadata_column insdc_secondary_accession --metadata_column dev_stage \
		--metadata_column description --metadata_column estimated_age --metadata_column sampling_date
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset CREOLE_INIA_UY.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--id_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset CORRIEDALE_INIA_UY.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--id_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset MERINO_INIA_UY.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--id_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset TEXEL_INIA_UY.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--id_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset Placa_Junio_recommended.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--alias_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset OP829-924_INIA_Abril.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--alias_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset Placas1_4_genotyping.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates_FINAL_fix.xlsx \
		--alias_column ID --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Smarter_Ids_Uploaded_with_GPSCordinates_FINAL.zip \
		--dst_dataset Affymetrix_data_Plate_652_660.zip --datafile Smarter_Ids_Uploaded_with_GPSCordinates2_FINAL_fix.xlsx \
		--alias_column "Sample Filename" --latitude_column Latitude --longitude_column Longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset Inia_junio_2021_Texel_46_20210409_SMARTER.zip --datafile 20210409_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP635-818 genotyping_soloTexel_20211110_SMARTER.zip" --datafile 20211110_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip --datafile 20210824_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP829-924 INIA Abril_20220301_Texel_SMARTER.zip" --datafile 20220301_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.zip" --datafile 20220323_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset INIA_other_WPs_metadata.zip \
		--dst_dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip" --datafile 20220810_Genexa_fix.xlsx \
		--id_column ID --latitude_column latitude --longitude_column longitude --metadata_column Stall \
		--metadata_column GPS_2
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_muflon_metadata.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude --metadata_column biosamples_id \
		--metadata_column sample_accession --metadata_column sample_provider --metadata_column closest_city \
		--metadata_column closest_locality --metadata_column estimated_age_months --metadata_column sampling_date
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset 41598_2017_7382_MOESM2_ESM.zip \
		--datafile 41598_2017_7382_MOESM2_ESM/barbato_sheep_metadata.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude --metadata_column biosamples_id \
		--metadata_column sample_accession --metadata_column sample_provider --metadata_column closest_city \
		--metadata_column closest_locality --metadata_column estimated_age_months --metadata_column sampling_date
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Ciani_2020.zip \
		--datafile 8947346/ciani_2020_metadata_fix.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude --metadata_column region \
		--metadata_column Type
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset northwest_africa_sheep.zip \
		--datafile northwest_africa_sheep/belabdi_2019_metadata.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude --metadata_column age \
		--metadata_column identification
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset gaouar_algerian_sheeps.zip \
		--datafile AlgerianSheep/gaouar_2017_metadata_fix.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude --metadata_column Site \
		--notes_column Note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset burren_et_al_2016.zip \
		--datafile doi_10.5061_dryad.q1cv6__v1/burren_phenotypes_fix.xlsx --breed_column breed \
		--metadata_column rare --notes_column note
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset SMARTER_CHFR_phenotypes.zip \
		--dst_dataset SMARTER_CHFR.zip --datafile SMARTER_CHFR_phenotypes/pierre_animals.xlsx \
		--id_column original_id --metadata_column animal_id --metadata_column lab_id \
		--metadata_column owner --metadata_column milk_recording --sex_column sex
	$(PYTHON_INTERPRETER) src/data/import_metadata.py --src_dataset Guisandesa.zip \
		--datafile Guisandesa/Guisandesa.xlsx --id_column original_id \
		--latitude_column latitude --longitude_column longitude

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
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset burren_et_al_2016.zip \
		--datafile doi_10.5061_dryad.q1cv6__v1/burren_phenotypes_fix.xlsx --breed_column breed \
		--additional_column coat_color --additional_column hair --additional_column horns \
		--additional_column size_male --additional_column size_female --additional_column performance
	$(PYTHON_INTERPRETER) src/data/import_multiple_phenotypes.py \
		--src_dataset "Smarter - Grazing behaviour phenotypes - Boutsko sheep.zip" \
		--dst_dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--datafile "Smarter - Grazing behaviour phenotypes - Boutsko sheep.xlsx" --id_column id \
		--column daily_activity_min --column daily_distance_km --column mean_speed_moving_m \
		--column altitude_difference_m --column elevation_gain_m --column energy_expenditure_MJ
	$(PYTHON_INTERPRETER) src/data/import_multiple_phenotypes.py \
		--src_dataset "Smarter - Grazing behaviour phenotypes - Boutsko sheep.zip" \
		--dst_dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip \
		--datafile "Smarter - Grazing behaviour phenotypes - Boutsko sheep.xlsx" --id_column id \
		--column daily_activity_min --column daily_distance_km --column mean_speed_moving_m \
		--column altitude_difference_m --column elevation_gain_m --column energy_expenditure_MJ
	$(PYTHON_INTERPRETER) src/data/import_phenotypes.py --src_dataset SMARTER_CHFR_phenotypes.zip \
		--dst_dataset SMARTER_CHFR.zip --datafile SMARTER_CHFR_phenotypes/pierre_animals.xlsx \
		--id_column original_id --chest_girth_column chest_size --height_column withers_height \
		--length_column body_length --additional_column pool_width --additional_column ear_length \
		--additional_column cannon_tower --additional_column teat_length --additional_column foot_opening \
		--additional_column jaw --additional_column horns --additional_column tassels \
		--additional_column front_udder_attachment --additional_column udder_profile \
		--additional_column udder_florr_position --additional_column teat_form \
		--additional_column teat_tilt --additional_column teat_orientation \
		--additional_column back_shape_udder --additional_column rear_udder_attachment
	$(PYTHON_INTERPRETER) src/data/import_multiple_phenotypes.py --src_dataset SMARTER_CHFR_phenotypes.zip \
		--dst_dataset SMARTER_CHFR.zip --datafile SMARTER_CHFR_phenotypes/milk_recording.xlsx \
		--id_column original_id --column date_of_control --column livestock_number \
		--column lactation_number --column milk_day --column milk_morning \
		--column average_somatics_cells --column somatics_cells_morning \
		--column average_fat_contents --column fat_contents_morning \
		--column proteic_contents_average --column proteic_contents_morning \
		--column urea_average --column urea_morning

	## merge SNPs into 1 file
	$(foreach ASSEMBLY, $(SHEEP_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class sheep --assembly $(ASSEMBLY);)
	$(foreach ASSEMBLY, $(GOAT_ASSEMBLIES), $(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class goat --assembly $(ASSEMBLY);)

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

	## SHEEP OAR4
	$(eval BASENAME=SMARTER-OA-OAR4-top-$(CURRENT_VERSION))
	cd ./data/processed/OAR4 && if [ -e $(BASENAME).zip ]; then rm $(BASENAME).zip; fi
	cd ./data/processed/OAR4 && zip -rvT $(BASENAME).zip $(BASENAME).bed $(BASENAME).bim $(BASENAME).fam $(BASENAME).hh $(BASENAME).log $(BASENAME).nosex
	cd ./data/processed/OAR4 && md5sum $(BASENAME).zip > $(BASENAME).md5
	find ./data/processed/OAR4 -type f \( -name "*.bed" -or -name "*.bim" -or -name "*.fam" -or -name "*.hh" -or -name "*.log" -or -name "*.nosex" \) -delete

	## GOAT ARS1
	$(eval BASENAME=SMARTER-CH-ARS1-top-$(CURRENT_VERSION))
	cd ./data/processed/ARS1 && if [ -e $(BASENAME).zip ]; then rm $(BASENAME).zip; fi
	cd ./data/processed/ARS1 && zip -rvT $(BASENAME).zip $(BASENAME).bed $(BASENAME).bim $(BASENAME).fam $(BASENAME).hh $(BASENAME).log $(BASENAME).nosex
	cd ./data/processed/ARS1 && md5sum $(BASENAME).zip > $(BASENAME).md5
	find ./data/processed/ARS1 -type f \( -name "*.bed" -or -name "*.bim" -or -name "*.fam" -or -name "*.hh" -or -name "*.log" -or -name "*.nosex" \) -delete

	## GOAT CHI1
	$(eval BASENAME=SMARTER-CH-CHI1-top-$(CURRENT_VERSION))
	cd ./data/processed/CHI1 && if [ -e $(BASENAME).zip ]; then rm $(BASENAME).zip; fi
	cd ./data/processed/CHI1 && zip -rvT $(BASENAME).zip $(BASENAME).bed $(BASENAME).bim $(BASENAME).fam $(BASENAME).hh $(BASENAME).log $(BASENAME).nosex
	cd ./data/processed/CHI1 && md5sum $(BASENAME).zip > $(BASENAME).md5
	find ./data/processed/CHI1 -type f \( -name "*.bed" -or -name "*.bim" -or -name "*.fam" -or -name "*.hh" -or -name "*.log" -or -name "*.nosex" \) -delete

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
	conda create --name $(PROJECT_NAME) --file conda-linux-64.lock
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
	coverage run --source src -m pytest
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
