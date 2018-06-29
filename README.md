### develop

Install Python 3 and virtualenv, then

```
$ make
```

To run a sanity-checking example

```
$ make debug
```

### batch processing

Add the `.csv` files to the `csvs` directory, then run `make pre` (this initializes the progress table)

To start iterating through all `(lat, lng)` coordinates in the `progress` table, saving progress as it goes,

```
$ make start
```
