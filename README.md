# OSM Scene

Transforming [OpenStreetMap](https://www.openstreetmap.org/) data.

## Configuration

This repository uses [pre-commit](https://pre-commit.com/).

Other configuration is primarily defined in [pyproject.toml](./pyproject.toml).

| Tool | Link |
| ---- | ---- |
| coverage | https://coverage.readthedocs.io/en/latest/config.html |
| pytest | https://docs.pytest.org/en/stable/reference/customize.html |
| ruff | https://docs.astral.sh/ruff/configuration/ |

## Scripts

### Run JOSM in Docker Container

> If needed, [install Docker](https://docs.docker.com/engine/install/).

```sh
./scripts/josm.sh
```

## Installation

> requires python3.12
>
> poetry 2.1.1 was used for development

```sh
pip install poetry==2.1.1
poetry install
```

and to contribute or to use the [python notebooks](./notebooks/README.md), install with the `dev` and/or `notebook` dependency groups, respectively.

```sh
poetry install --with dev,notebook
```

## Main Executable

The easiest strategy for using the app is by editing [.env](./.env) with configuration parameters.

**e.g.**

```
OSM_SCENE_DIR_IN="io"
OSM_SCENE_DIR_OUT="io"
OSM_SCENE_Q={"e2": [100, 100], "origin": [52.518403, 13.358893]}
```

After replacing [env](./.env) file contents, confirm that the package is installed with

### Query

```sh
osm_scene query
```

### Build

```sh
osm_scene build
```

### Get more details

```sh
osm_scene --help
```

or just...

```sh
osm_scene
```

## Supporting New Tags

> https://wiki.openstreetmap.org/wiki/Taginfo/API
>
> https://taginfo.openstreetmap.org/taginfo/apidoc

```py
import requests

response = requests.get(
    "https://taginfo.openstreetmap.org/api/4/key/values?key=highway&filter=ways&sortname=count_ways&sortorder=desc",
)
response.json()
```
