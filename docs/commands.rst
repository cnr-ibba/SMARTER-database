Commands
========

.. contents:: Table of Contents

Here are the scripts called during data import by the ``make initialize``
and ``make data`` commands. For more information, see
:ref:`The Data Import Process` and :ref:`Loading variants into database`
documentation sections.

.. _add_breed:

.. click:: src.data.add_breed:main
    :prog: src/data/add_breed.py
    :nested: full

.. _import_affymetrix:

.. click:: src.data.import_affymetrix:main
    :prog: src/data/import_affymetrix.py
    :nested: full

.. _import_breeds:

.. click:: src.data.import_breeds:main
    :prog: src/data/import_breeds.py
    :nested: full

.. _import_consortium:

.. click:: src.data.import_consortium:main
    :prog: src/data/import_consortium.py
    :nested: full

.. _import_datasets:

.. click:: src.data.import_datasets:main
    :prog: src/data/import_datasets.py
    :nested: full

.. _import_from_affymetrix:

.. click:: src.data.import_from_affymetrix:main
    :prog: src/data/import_from_affymetrix.py
    :nested: full

.. _import_from_illumina:

.. click:: src.data.import_from_illumina:main
    :prog: src/data/import_from_illumina.py
    :nested: full

.. _import_from_plink:

.. click:: src.data.import_from_plink:main
    :prog: src/data/import_from_plink.py
    :nested: full

.. _import_manifest:

.. click:: src.data.import_manifest:main
    :prog: src/data/import_manifest.py
    :nested: full

.. _import_metadata:

.. click:: src.data.import_metadata:main
    :prog: src/data/import_metadata.py
    :nested: full

.. _import_phenotypes:

.. click:: src.data.import_phenotypes:main
    :prog: src/data/import_phenotypes.py
    :nested: full

.. _import_samples:

.. click:: src.data.import_samples:main
    :prog: src/data/import_samples.py
    :nested: full

.. _import_snpchimp:

.. click:: src.data.import_snpchimp:main
    :prog: src/data/import_snpchimp.py
    :nested: full

.. _import_snpchips:

.. click:: src.data.import_snpchips:main
    :prog: src/data/import_snpchips.py
    :nested: full

.. _merge_datasets:

.. click:: src.data.merge_datasets:main
    :prog: src/data/merge_datasets.py
    :nested: full
