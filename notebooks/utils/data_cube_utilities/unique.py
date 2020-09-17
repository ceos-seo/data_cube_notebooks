def dask_array_uniques(arr):
    """
    Returns the unique values for a Dask Array object.
    
    Parameters
    ----------
    arr: dask.array.core.Array
    
    Returns
    -------
    uniques: numpy.ndarray
    """
    import dask

    return dask.dataframe.from_dask_array(arr.flatten())\
           .drop_duplicates().to_dask_array(lengths=True).compute()