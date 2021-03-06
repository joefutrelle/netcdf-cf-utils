import calendar

import numpy as np

FILL_VALUE = -9999.9

TIME_VAR = 'time'
LAT_VAR = 'latitude'
LON_VAR = 'longitude'
DEPTH_VAR = 'depth'
PLATFORM_VAR = 'platform'
INSTRUMENT_VAR = 'instrument'

def datetimes2unixtimes(dts):
    """:param times: a datetime64 array, Series, or Index.
    returns float array of s since UNIX epoch"""
    # convert datetime to floating point s since UNIX epoch
    return np.asarray([calendar.timegm(x.utctimetuple()) for x in dts]).astype(np.float)

def unixtimes2datetimes(times):
    """:param times: float array of s since UNIX epoch"""
    return pd.to_datetime(times * 10e8)

def setncattrs(obj, attr_dict):
    for k, v in attr_dict.items():
        obj.setncattr(k, v)
        
class CFWriter(object):
    def __init__(self, ds):
        """:param ds: netCDF4 Dataset"""
        self.ds = ds

    def create_crs_var(self, name='crs'):
        crs = self.ds.createVariable(name, np.float)
        crs.grid_mapping_name = 'latitude_longitude'
        crs.longitude_of_prime_meridian = 0.
        crs.semi_major_axis = 6378137.
        crs.inverse_flattening = 298.257223563
        crs.epsg_code = 'EPSG:4326'
        crs = 0.
        return crs

    def create_empty_var(self, name, attributes={}):
        ev = self.ds.createVariable(name,'S1')
        ev.long_name = name
        setncattrs(ev, attributes)
        ev = ''
        return ev

    def get_feature_vars(self, feature_type):
        """cdm vars include a feature type var and
        x/y/z, platform, instrument."""
        return ', '.join([
            feature_type,
            LAT_VAR,
            LON_VAR,
            DEPTH_VAR,
            PLATFORM_VAR,
            INSTRUMENT_VAR
            ])
    
    def create_id_var(self, name, long_name=None, attributes={}):
        """create a name with a {}_id cf_role"""
        cf_role = '{}_id'.format(name)
        dim_name = '{}_dim'.format(name)
        if long_name is None:
            long_name = name
        self.ds.createDimension(dim_name, size=len(long_name))
        idvar = self.ds.createVariable(name, 'S1', (dim_name,))
        idvar.cf_role = cf_role
        idvar.long_name = long_name
        setncattrs(idvar, attributes)
        idvar[:] = list(long_name)
        return idvar

    def create_time_var(self, times, dimensions=None):
        if dimensions is None:
            dimensions = ('time',)
        """creates time dimension and time variable.
        units are floating point s since unix epoch"""
        # call the dimension and variable the same thing
        self.ds.createDimension('time', size=len(times))
        t = self.ds.createVariable('time', times.dtype, dimensions)
        t.units = 'seconds since 1970-01-01T00:00:00Z'
        t.standard_name = 'time'
        t.long_name = 'time'
        t.calendar = 'gregorian' # is this correct?
        t.axis = 'T'
        t[:] = times
        return t

    def create_lat_var(self, dimensions=()):
        vlat = self.ds.createVariable(LAT_VAR, np.float, dimensions)
        vlat.long_name = LAT_VAR
        vlat.standard_name = LAT_VAR
        vlat.units = 'degrees_north'
        vlat.valid_min = -90.
        vlat.valid_max = 90.
        vlat.axis = 'Y'
        return vlat

    def create_lon_var(self, dimensions=()):
        vlon = self.ds.createVariable(LON_VAR, np.float, dimensions)
        vlon.long_name = LON_VAR
        vlon.standard_name = LON_VAR
        vlon.units = 'degrees_east'
        vlon.valid_min = -180.
        vlon.valid_max = 180.
        vlon.axis = 'X'
        return vlon

    def create_depth_var(self, dimensions=()):
        vdepth = self.ds.createVariable(DEPTH_VAR, np.float, dimensions)
        vdepth.long_name = DEPTH_VAR
        vdepth.standard_name = DEPTH_VAR
        vdepth.units = 'm'
        vdepth.positive = 'down'
        vdepth.axis = 'Z'
        vdepth.valid_min = 0.
        vdepth.valid_max = 10971.
        return vdepth

    def create_var(self, name, values, dimensions, fill_value=FILL_VALUE, valid_range=None, units=None):
        v = self.ds.createVariable(name, values.dtype, dimensions, fill_value=fill_value)
        v.long_name = name
        v.standard_name = name
        if valid_range is not None:
            v.valid_min, v.valid_max = valid_range
        if units is None:
            units = '1'
        v.units = units
        v[:] = np.array(values)
        return v

    def create_platform_var(self, attributes={}):
        return self.create_empty_var(PLATFORM_VAR, attributes)

    def create_instrument_var(self, attributes={}):
        return self.create_empty_var(INSTRUMENT_VAR, attributes)

    def create_obs_vars(self, df, dimensions, units):
        for varname in df.columns:
            u = units if type(units) is str else units.get(varname)
            v = self.create_var(varname, df[varname], dimensions=dimensions, units=u)
            v.coordinates = ' '.join([TIME_VAR, DEPTH_VAR, LAT_VAR, LON_VAR])
            v.grid_mapping = 'crs'
            v.platform = PLATFORM_VAR
            v.instrument = INSTRUMENT_VAR
