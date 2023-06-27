
# This is a supplementary file for Makefile used to make data for additional
# assemblies. Samples are supposed to have been created

assemblies:
	# convert genotypes without creating samples in database (SHEEP)
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file TEXEL_UY --dataset TEXEL_INIA_UY.zip --chip_name IlluminaOvineSNP50 \
		--assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Frizarta54samples_ped_map_files/Frizarta54samples \
		--dataset Frizarta54samples_ped_map_files.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file MERINO_UY_96_21_12_17_OV54k \
		--dataset MERINO_INIA_UY.zip --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file CORRIEDALE_UY_60_INIA_Ovine_14sep2010 \
		--dataset CORRIEDALE_INIA_UY.zip --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport1.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL --chip_name IlluminaOvineHDSNP --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report JCM2357_UGY_FinalReport2.txt --snpfile OvineHDSNPList.txt \
		--dataset CREOLE_INIA_UY.zip --breed_code CRL --chip_name IlluminaOvineHDSNP --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile frenchsheep_HD \
		--dataset "High density genotypes of French Sheep populations.zip" --chip_name IlluminaOvineHDSNP --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file ovine_SNP50HapMap_data/SNP50_Breedv1/SNP50_Breedv1 \
		--dataset ovine_SNP50HapMap_data.zip --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_OVIS_FRANCE \
		--dataset "SMARTER_OVIS_FRANCE.zip" --chip_name IlluminaOvineHDSNP --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SWE_sheep \
		--dataset "five_sweden_sheeps.zip" --chip_name IlluminaOvineHDSNP --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file friz \
		--dataset Frizarta_270.zip --coding ab --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file SMARTER-500-ASSAF --dataset SMARTER-500-ASSAF.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR4 --search_field probeset_id  \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "Castellana/20220131 Ovine" --dataset Castellana.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR4 --search_field probeset_id  \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220326_resultados_SNP/20220326_Ovine" --dataset 20220326_resultados_SNP.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR4 --search_field probeset_id  \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220428_Smarter_Ovine/20220428_Smarter_Ovine" --dataset 20220428_Smarter_Ovine.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR4 --search_field probeset_id  \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "20220503_Ovine/20220503_Ovine" --dataset 20220503_Ovine.zip \
		--coding affymetrix --chip_name AffymetrixAxiomBGovisNP --assembly OAR4 --search_field probeset_id  \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_652/Affymetrix_data_Plate_652 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR4 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --prefix Affymetrix_data_Plate_652_660/Affymetrix_data_Plate_660/Affymetrix_data_Plate_660 \
		--dataset Affymetrix_data_Plate_652_660.zip --breed_code CRR --chip_name AffymetrixAxiomOviCan --assembly OAR4 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA/AUTH_OVN50KV2_CHI_FRI \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA/AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA \
		--dataset AUTH_OVN50KV2_CHIOS_FRIZARTA_PELAGONIA.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/Aristotle_University_OVN50KV02_20210720_FinalReport.txt \
		--snpfile AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO/SNP_Map.txt --dataset AUTH_OVN50KV2_CHIOS_MYTILINI_BOUTSKO.zip \
		--chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50KV2_CHI_BOU_MYT_FRI/Aristotle_University_OVN50KV02_20211108 \
		--dataset AUTH_OVN50KV2_CHI_BOU_MYT_FRI.zip --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile AUTH_OVN50K2_CHI_FRZ/Aristotle_University_OVN50KV02_20211124 \
		--dataset AUTH_OVN50KV2_CHI_FRZ.zip --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file NativesheepBreeds_Hu/NativeSheepGenotypes \
		--dataset NativesheepBreeds_Hu.zip --coding forward --chip_name IlluminaOvineSNP50 --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file Churra/churra_fixed \
		--dataset Churra.zip --coding affymetrix --chip_name AffymetrixAxiomBGovis2 --assembly OAR4 \
		--src_version Oar_v3.1 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placa_Junio_recommended.txt \
		--dataset Placa_Junio_recommended.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP829-924 INIA Abril.txt" \
		--dataset OP829-924_INIA_Abril.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placas1_4_genotyping.txt \
		--dataset Placas1_4_genotyping.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 --sample_field alias \
		--src_version Oar_v4.0 --src_imported_from affymetrix
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 50K-all \
		--dataset isheep_50K.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 \
		--search_field rs_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 600K-all \
		--dataset isheep_600K.zip --coding top --chip_name IlluminaOvineHDSNP --assembly OAR4 --sample_field alias \
		--search_field rs_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile WGS-all.smarter \
		--dataset isheep_WGS.zip --coding forward --chip_name WholeGenomeSequencing --assembly OAR4 --sample_field alias \
		--search_by_positions --src_version Oar_v4.0 --src_imported_from "SNPchiMp v.3" --ignore_coding_errors
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file ovine_SNP50HapMap_data/SNP50_Breedv2/SNP50_Breedv2 \
		--dataset ovine_SNP50HapMap_data.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Inia_junio_2021_Texel_46_20210409_SMARTER.txt \
		--dataset Inia_junio_2021_Texel_46_20210409_SMARTER.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 38
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP635-818 genotyping_soloTexel_20211110_SMARTER.txt" \
		--dataset "OP635-818 genotyping_soloTexel_20211110_SMARTER.zip" --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 59
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.txt \
		--dataset Placas1_4_genotyping_Corr_Tex_20210824_SMARTER.zip --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 332
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP829-924 INIA Abril_20220301_Texel_SMARTER.txt" \
		--dataset "OP829-924 INIA Abril_20220301_Texel_SMARTER.zip" --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 43
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.txt" \
		--dataset "OP925-969 1046-1085 1010-1020_20220323_texel_SMARTER.zip" --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 25
	$(PYTHON_INTERPRETER) src/data/import_from_affymetrix.py --report "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.txt" \
		--dataset "OP1586-1666 OP1087-1106 Placa6 Corr_Tex_Genotyping_20220810_SMARTER.zip" --coding ab --chip_name AffymetrixAxiomOviCan --assembly OAR4 \
		--sample_field alias --src_version Oar_v4.0 --src_imported_from affymetrix --max_samples 35 --skip_coordinate_check
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file "genotyping data/WelshSheepBreeds2015" \
		--dataset Welsh_sheep_genotyping.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 41598_2017_7382_MOESM2_ESM/Barbato_2016 \
		--dataset 41598_2017_7382_MOESM2_ESM.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile 8947346/OaSNP1477x44430-1807 \
		--dataset Ciani_2020.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file northwest_africa_sheep/AlgerianSheepSidaounHamra \
		--dataset northwest_africa_sheep.zip --coding top --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file AlgerianSheep/AlgerianSheep \
		--dataset gaouar_algerian_sheeps.zip --coding illumina --chip_name IlluminaOvineSNP50 --assembly OAR4 --sample_field original_id \
		--src_version Oar_v4.0 --src_imported_from manifest

	## convert genotypes without creating samples in database (GOAT)
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --snpfile Swedish_Univ_Eriksson_GOAT53KV1_20200722/SNP_Map.txt \
		--report Swedish_Univ_Eriksson_GOAT53KV1_20200722/Swedish_Univ_Eriksson_GOAT53KV1_20200722_FinalReport.txt \
		--dataset Swedish_Univ_Eriksson_GOAT53KV1_20200722.zip --breed_code LNR --chip_name IlluminaGoatSNP50 --assembly CHI1
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile SMARTER_CHFR \
		--dataset SMARTER_CHFR.zip --chip_name IlluminaGoatSNP50 --assembly CHI1
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile ADAPTmap_genotypeTOP_20161201/binary_fileset/ADAPTmap_genotypeTOP_20161201 \
		--dataset "ADAPTmap_genotypeTOP_20161201.zip" --chip_name IlluminaGoatSNP50 --assembly CHI1
	$(PYTHON_INTERPRETER) src/data/import_from_illumina.py --report AUTH_GOAT53KV1_EGHORIA_SKOPELOS/Aristotle_University_GOAT53KV1_20200728_FinalReport.txt \
		--snpfile AUTH_GOAT53KV1_EGHORIA_SKOPELOS/SNP_Map.txt --dataset AUTH_GOAT53KV1_EGHORIA_SKOPELOS.zip \
		--chip_name IlluminaGoatSNP50 --assembly CHI1
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --file doi_10.5061_dryad.q1cv6__v1/goat_data2_dryad_fix \
		--dataset burren_et_al_2016.zip --chip_name IlluminaGoatSNP50 --assembly CHI1 --sample_field alias
	$(PYTHON_INTERPRETER) src/data/import_from_plink.py --bfile s41598-021-89900-2/Cortellari2021 \
		--dataset cortellari_et_al_2021.zip --chip_name IlluminaGoatSNP50 --assembly CHI1

	## merge SNPs into 1 file
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class sheep --assembly OAR4
	$(PYTHON_INTERPRETER) src/data/merge_datasets.py --species_class goat --assembly CHI1
