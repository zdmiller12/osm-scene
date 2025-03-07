# OSM Scene

Transforming [OpenStreetMap](https://www.openstreetmap.org/) data.

## Scripts

### Run JOSM in Docker Container

> If needed, [install Docker](https://docs.docker.com/engine/install/).

```sh
./scripts/josm.sh
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

```sh
poetry install
```

> python ~3.12

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
