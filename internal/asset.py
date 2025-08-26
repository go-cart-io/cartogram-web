import json
import os
from urllib.parse import urlparse

import settings
from flask import current_app


class Asset:
    CDN_LIST = {
        "common": ["@popperjs/core", "bootstrap"],
        "app": ["vue", "d3", "vega", "vega-embed", "vega-tooltip"],
    }

    def __init__(self, app=None):
        self.app = app
        self.manifest = {}
        self.pkg = {}
        self.cdn = {}
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.manifest_path = os.path.join(
            app.static_folder, "dist", ".vite", "manifest.json"
        )
        self._load_webpack_assets(app)
        self._load_package_and_cdn_json(app)

        if settings.IS_DEBUG:
            app.before_request(self.reload_webpack_assets)

        app.context_processor(lambda: {"asset": self})

    def reload_webpack_assets(self):
        self._load_webpack_assets(current_app)

    def _load_webpack_assets(self, app):
        with app.open_resource(self.manifest_path) as manifest_file:
            self.manifest = json.load(manifest_file)

    def _load_package_and_cdn_json(self, app):
        package_path = os.path.join(app.root_path, "..", "frontend", "package.json")
        with open(package_path, "r") as f:
            self.pkg = json.load(f)

        cdn_path = os.path.join(app.root_path, "..", "frontend", "cdn-packages.json")
        with open(cdn_path, "r") as f:
            cdn_json = json.load(f)
            self.cdn = {pkg["name"]: pkg["path"] for pkg in cdn_json}

    def all_vite_assets(self, entry_name):
        """Get CSS and JS assets for a specific entry point"""
        assets = {"css": [], "js": []}

        if entry_name in self.manifest:
            entry = self.manifest[entry_name]

            # Add imported chunks (like vendor.js)
            if "imports" in entry:
                for import_key in entry["imports"]:
                    if import_key in self.manifest:
                        import_entry = self.manifest[import_key]
                        if "file" in import_entry:
                            assets["js"].append(f"dist/{import_entry['file']}")
                        if "css" in import_entry:
                            for css_file in import_entry["css"]:
                                assets["css"].append(f"dist/{css_file}")

            # Add main JS file
            if "file" in entry:
                assets["js"].append(f"dist/{entry['file']}")

            # Add CSS files
            if "css" in entry:
                for css_file in entry["css"]:
                    assets["css"].append(f"dist/{css_file}")

        return assets

    def all_cdn_scripts(self, name) -> list[str]:
        return [self.cdn_url_for(pkg) for pkg in self.CDN_LIST.get(name, "")]

    def url_for(self, file):
        return self.manifest.get(file)

    def webpack_url_for(self, base_url, file):
        o = urlparse(base_url)
        port = (
            settings.VITE_SERVER_PORT
            if settings.VITE_SERVER_PORT is not None
            else "5173"
        )
        return "//" + o.hostname + ":" + port + "/" + file

    def cdn_url_for(self, package_name):
        """Get CDN URL for a package with version from package.json"""
        file_path = "/" + self.cdn[package_name] if self.cdn[package_name] else ""

        version = self.pkg.get("dependencies", {}).get(package_name, "latest")
        version = version.lstrip("^~")  # Remove ^ or ~ from version if present

        return f"https://cdn.jsdelivr.net/npm/{package_name}@{version}{file_path}"
