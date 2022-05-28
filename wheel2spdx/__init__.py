import argparse
from datetime import datetime
import io
import os
import sys
from typing import Optional

from distlib.database import DistributionPath
from distlib.metadata import Metadata
from distlib.wheel import Wheel
from spdx.creationinfo import Person
from spdx.document import Document, License
from spdx.package import Package
from spdx.version import Version
from spdx.writers import rdf


def convert_metadata(
    metadata: Metadata,
    filename: Optional[str] = None,
) -> Package:
    metadata_dict = metadata.todict()
    spdx_package = Package(
        name=metadata.name,
        version=metadata.version,
        spdx_id=metadata.name_and_version,
        download_location=metadata.source_url,
        supplier=Person(
            metadata_dict.get("author"),
            metadata_dict.get("author_email"),
        ),
        file_name=os.path.basename(filename) if filename else None,
    )
    homepage: Optional[str] = None
    if "home_page" in metadata_dict:
        homepage = metadata_dict["home_page"]
    elif "project_url" in metadata_dict:
        homepage = metadata_dict["project_url"][0].split(",", 1)[1].strip()
    spdx_package.homepage = homepage
    spdx_package.summary = metadata.summary
    spdx_package.description = metadata_dict.get("description")

    license = License.from_identifier(metadata.license)
    spdx_package.conc_lics = license
    spdx_package.license_declared = license
    return spdx_package


def convert_wheel(filename: str) -> Document:
    whl = Wheel(filename=filename)
    metadata: Metadata = whl.metadata
    spdx_package = convert_metadata(metadata, filename)
    spdx_document = Document(
        data_license=License.from_identifier("MIT"),
        package=spdx_package,
        version=Version(2, 2),
        name=metadata.name,
    )
    spdx_document.creation_info.created = datetime.now()
    return spdx_document


def convert_site_packages() -> Document:
    dist_path = DistributionPath()
    dists = dist_path.get_distributions()
    spdx_packages = [convert_metadata(dist.metadata) for dist in dists]
    spdx_document = Document(
        data_license=License.from_identifier("MIT"),
        version=Version(2, 2),
        name="site-packages",
    )
    spdx_document.packages.extend(spdx_packages)
    spdx_document.creation_info.created = datetime.now()
    return spdx_document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel")
    args = parser.parse_args()
    if args.wheel:
        spdx = convert_wheel(args.wheel)
    else:
        spdx = convert_site_packages()
    out = io.BytesIO()
    rdf.write_document(spdx, out, False)
    sys.stdout.buffer.write(out.getvalue())
