
import sys
import shutil

REQUIRED_PYTHON = "python3"
REQUIRED_SOFTWARES = [
    'plink',
    'tabix',
    'vcftools'
]


def main():
    system_major = sys.version_info.major
    if REQUIRED_PYTHON == "python3":
        required_major = 3

    else:
        raise ValueError("Unrecognized python interpreter: {}".format(
            REQUIRED_PYTHON))

    if system_major != required_major:
        raise TypeError(
            "This project requires Python {}. Found: Python {}".format(
                required_major, sys.version))

    # test for software dependencies
    path = dict()

    for software in REQUIRED_SOFTWARES:
        path[software] = shutil.which(software)

    if None in path.values():
        for key, value in path.items():
            if value is None:
                print(f"{key} is required for analyses")

        raise Exception(
            "This project requires some software installed!"
        )

    print(">>> Development environment passes all tests!")


if __name__ == '__main__':
    main()
