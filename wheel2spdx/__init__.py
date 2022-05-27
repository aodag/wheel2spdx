import argparse
from datetime import datetime
import io
import os
import sys

from distlib.wheel import Wheel
from distlib.metadata import Metadata
from spdx.creationinfo import Person
from spdx.document import Document, License
from spdx.package import Package
from spdx.version import Version
from spdx.writers import rdf


def convert(filename: str) -> Document:
    whl = Wheel(filename=filename)
    metadata: Metadata = whl.metadata
    metadata_dict = metadata.todict()
    print(metadata_dict)
    spdx_package = Package(
        name=metadata.name,
        version=metadata.version,
        spdx_id=metadata.name_and_version,
        file_name=os.path.basename(filename),
        download_location=metadata.source_url,
        supplier=Person(
            metadata_dict.get("author"),
            metadata_dict.get("author_email"),
        ),
    )
    homepage = metadata_dict["project_url"][0].split(",", 1)[1].strip()
    spdx_package.homepage = homepage
    spdx_package.summary = metadata.summary
    spdx_package.description = metadata_dict.get("description")
    license = License.from_identifier(metadata.license)
    spdx_package.conc_lics = license
    spdx_package.license_declared = license
    spdx_document = Document(
        data_license=License.from_identifier("MIT"),
        package=spdx_package,
        version=Version(2, 2),
        name=metadata.name,
    )
    spdx_document.creation_info.created = datetime.now()
    return spdx_document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    spdx = convert(args.file)
    out = io.BytesIO()
    rdf.write_document(spdx, out, False)
    sys.stdout.buffer.write(out.getvalue())
