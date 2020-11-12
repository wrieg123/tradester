from django.db import models


class providers(models.Model):
    provider = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length = 190, null = False)
    api_keys = models.TextField(blank = True, null = True)
    comments = models.TextField(blank = True, null = True)

    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    class Meta:
        db_table = "providers"

class currencies(models.Model):
    currency = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length = 190, null = False)
    description = models.TextField(blank=True, null = True)
    mappings = models.CharField(max_length = 190, null = True) 

    daily_start_date = models.DateField(null = True)
    daily_end_date = models.DateField(null = True)

    def __str__(self):
        return f"{self.name} ({self.currency})"

    class Meta:
        db_table = 'currencies'


class exchanges(models.Model):
    exchange = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length =190, null = False)
    
    def __str__(self):
        return f"{self.name} ({self.exchange})"

    class Meta:
        db_table = 'exchanges'


class countries(models.Model):
    country = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length = 190, null = False)
    currency = models.ForeignKey(currencies, on_delete = models.CASCADE, null = True, db_column = 'currency')
    em_dm_fm = models.CharField(max_length = 2, null = True)
    is_key_market = models.BooleanField(default = False, null = True)
    is_brics = models.BooleanField(default = False, null = True)
    is_n11 = models.BooleanField(default = False, null = True)
    is_g7 = models.BooleanField(default = False, null = True)
    is_g10 = models.BooleanField(default = False, null = True)
    is_g20 = models.BooleanField(default = False, null = True)
    main_bourse = models.CharField(max_length = 190, null = True)
    main_index = models.CharField(max_length = 190, null = True)
    bond_tr = models.CharField(max_length = 190, null = True)

    def __str__(self):
        return f"{self.name} ({self.country})"

    class Meta:
        db_table = 'countries'


class products(models.Model):
    product = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length = 190, null = False)
    product_group = models.CharField(max_length = 190, null = True)
    sub_group = models.CharField(max_length = 190, null = True)
    category = models.CharField(max_length = 190, null = True)
    sub_category = models.CharField(max_length = 190, null = True)
    exchange = models.ForeignKey(exchanges, on_delete = models.CASCADE, db_column = 'exchange', null = True)
    
    # General Identifiers
    eikon_map = models.CharField(max_length = 190, null = True)
    barchart_map = models.CharField(max_length = 190, null = True)
    multiplier = models.FloatField(null = True)
    listed_months = models.CharField(max_length = 190, null = True)
    first_seen = models.CharField(max_length = 190, null = True)
    list_out = models.IntegerField(null = True)
    
    # CME specs, if available
    globex = models.CharField(max_length = 190, null = True)
    clearport = models.CharField(max_length = 190, null = True)
    clearing = models.CharField(max_length = 190, null = True)

    def __str__(self):
        return f"{self.name} ({self.product})"
    
    class Meta:
        db_table = 'products'

class sectors(models.Model):
    """Meta table related to sector descriptions (corresponds to L4_sector)"""
    sector = models.IntegerField(primary_key = True)
    name = models.CharField(max_length = 190, null = False)
    main_index = models.CharField(max_length = 190, null = True)

    class Meta:
        db_table = 'sectors'

class industry_groups(models.Model):
    industry_group = models.IntegerField(primary_key = True)
    sector = models.ForeignKey(sectors, on_delete = models.CASCADE, db_column = 'sector', null = False)
    name = models.CharField(max_length = 190, null = False)
    main_index = models.CharField(max_length = 190, null = True)

    class Meta:
        db_table = 'industry_groups'

class industries(models.Model):
    industry = models.IntegerField(primary_key = True)
    industry_group = models.ForeignKey(industry_groups, on_delete = models.CASCADE, db_column = 'industry_group', null = False)
    sector = models.ForeignKey(sectors, on_delete = models.CASCADE, db_column = 'sector', null = False)
    name = models.CharField(max_length = 190, null = False)
    main_index = models.CharField(max_length = 190, null = True)

    class Meta:
        db_table = 'industries'

class sub_industries(models.Model):
    sub_industry = models.IntegerField(primary_key = True)
    industry = models.ForeignKey(industries, on_delete = models.CASCADE, db_column = 'industry', null = False)
    industry_group = models.ForeignKey(industry_groups, on_delete = models.CASCADE, db_column = 'industry_group', null = False)
    sector = models.ForeignKey(sectors, on_delete = models.CASCADE, db_column = 'sector', null = False)
    name = models.CharField(max_length = 190, null = False)
    main_index = models.CharField(max_length = 190, null = True)

    class Meta:
        db_table = 'sub_industries'

# Economic Tracking Stuff
class symbols(models.Model):
    report_frequencies = [
        (None, None),    
        ('D', 'Daily'),
        ('W', 'Weekly'),
        ('BW', 'Bi-weekly'),
        ('M', 'Monthly'),
        ('Q', 'Quarterly'),
        ('Y', 'Yearly'),
    ]

    symbol = models.CharField(max_length = 190, primary_key = True)
    name = models.CharField(max_length = 190, null = True)
    description = models.TextField(blank = True, null = True)
    report_frequency = models.CharField(max_length = 190, choices = report_frequencies, null = True)
    report_lag = models.IntegerField(null = True, help_text = "Number of days to lag for server input availability")  
    provider = models.ForeignKey(providers, null = False, on_delete = models.CASCADE, db_column = 'provider', related_name = 'symbol_provider') 
    db = models.CharField(max_length = 190, null = True)
    table = models.CharField(max_length = 190, null = True)
    
    geography = models.CharField(max_length = 190, null = True)
    country = models.ForeignKey(countries, null = True, on_delete = models.CASCADE, db_column = 'country', related_name = 'symbol_country')
    region = models.CharField(max_length = 190, null = True)
    state = models.CharField(max_length = 190, null = True)
    field = models.CharField(max_length = 190, null = True)
    field_mod = models.CharField(max_length = 190, null = True)
    product = models.ForeignKey(products, null = True, on_delete = models.CASCADE, db_column = 'product', related_name = 'symbol_product')
    product_type = models.CharField(max_length = 190, null = True) 
    sub_industry = models.ForeignKey(sub_industries, on_delete = models.CASCADE, db_column = 'sub_industry', null = True)
    industry = models.ForeignKey(industries, on_delete = models.CASCADE, db_column = 'industry', null = True)
    industry_group = models.ForeignKey(industry_groups, on_delete = models.CASCADE, db_column = 'industry_group', null = True)
    sector = models.ForeignKey(sectors, on_delete = models.CASCADE, db_column = 'sector', null = True)

    date_updated = models.DateField(null = True, help_text = "Last day this item was checked for data")
    start_date_released = models.DateField(null = True)
    end_date_released = models.DateField(null = True)
    start_date_effective = models.DateField(null = True)
    end_date_effective = models.DateField(null = True)
    is_deprecated = models.BooleanField(null = False, default = False)

    class Meta:
        db_table = 'symbols'

class futures(models.Model):
    contract = models.CharField(max_length = 190, primary_key = True, help_text = "")
    name = models.CharField(max_length = 190, null = True)
    is_active = models.BooleanField(null = False, default = False)
    underlying = models.ForeignKey(products, on_delete = models.CASCADE, db_column = 'product')
    reference_contract = models.CharField(max_length = 190, null = True)
    provider = models.ForeignKey(providers, on_delete = models.CASCADE, db_column = 'provider')
    exchange = models.ForeignKey(exchanges, on_delete = models.CASCADE, db_column = 'exchange', default = 'CME')    
    mappings = models.CharField(max_length = 190, null = True)    
    currency = models.ForeignKey(currencies, on_delete = models.CASCADE, db_column = 'currency', default = 'USD')
    multiplier = models.FloatField(null = True)
    weight_multiplier_lb = models.FloatField(null = True)

    is_continuation = models.BooleanField(null = False, default = False)
    is_synthetic = models.BooleanField(null = True)
    continuation = models.IntegerField(null = True) 
    
    first_trade_date = models.DateField(null = True)
    last_trade_date =  models.DateField(null = True)
    settlement_date = models.DateField(null = True)
    soft_expiry = models.DateField(null = True)

    daily_start_date = models.DateField(null = True)
    daily_end_date = models.DateField(null = True)
    tick_start_date = models.DateTimeField(null = True)
    tick_end_date = models.DateTimeField(null = True)

    class Meta:
        db_table = 'futures'


class options(models.Model):
    contract = models.CharField(max_length = 190, primary_key = True, help_text = "")
    is_active = models.BooleanField(null = False, default = False)
    product = models.ForeignKey(products, null = True, on_delete = models.CASCADE, db_column = 'product')
    future = models.ForeignKey(futures, on_delete = models.CASCADE, db_column = 'future', null = True)
    exchange = models.ForeignKey(exchanges, on_delete = models.CASCADE, db_column = 'exchange')
    expiry = models.DateField(null = False)
    strike = models.FloatField(null = False)
    right = models.CharField(max_length = 190, choices = [('P', 'Put'), ('C', 'Call')], null = False)
    provider = models.ForeignKey(providers, on_delete = models.CASCADE, db_column = 'provider')
    daily_start_date = models.DateField(null = True)
    daily_end_date = models.DateField(null = True)
    tick_start_date = models.DateTimeField(null = True)
    tick_end_date = models.DateTimeField(null = True)
    mappings = models.CharField(max_length = 190, null = True)    
    currency = models.ForeignKey(currencies, on_delete = models.CASCADE, db_column = 'currency', default = 'USD')

    class Meta:
        db_table = 'options'

##### TIME SERIES TABLES ######



class ts_symbols(models.Model):
    date_released = models.DateField(null = False)
    date_effective = models.DateField(null = True)
    symbol = models.ForeignKey(symbols, on_delete = models.CASCADE, db_column = 'symbol', null = False)
    value = models.FloatField(null = False)
    is_revision = models.BooleanField(null = False, default= False)

    class Meta:
        db_table = 'ts_symbols'
        indexes = [
            models.Index(fields = ('date_released', 'symbol'), name = 'dr_symbol_idx'),
            models.Index(fields = ('date_effective', 'symbol'), name = 'de_symbol_idx')
        ]
        constraints = [
            models.UniqueConstraint(fields = ['date_released', 'date_effective', 'symbol' ],name = 'unique_dr_de_s'),
        ] 


class ts_covariance(models.Model):
    date = models.DateField(null = False)
    f_symbol = models.CharField(max_length = 190, null = False)
    t_symbol = models.CharField(max_length = 190, null = False)
    value = models.FloatField(null = False)

    class Meta:
        db_table = 'ts_covariance'
        indexes = [
            models.Index(fields = ('date', 'f_symbol', 't_symbol'), name = 'd_f_t_idx'),
            models.Index(fields = ('date', 'f_symbol'), name = 'd_f_idx'),
            models.Index(fields = ('date', 't_symbol'), name = 'd_t_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields = ('date', 'f_symbol','t_symbol'), name = 'unique_d_f_t'),
        ]

class ts_daily_futures(models.Model):
    date = models.DateField(null = False)
    contract = models.ForeignKey(futures, on_delete = models.CASCADE, db_column = 'contract')
    open = models.FloatField(null = True)
    high = models.FloatField(null = True)
    low = models.FloatField(null = True)
    close = models.FloatField(null = False)
    volume = models.FloatField(null = True)
    open_interest = models.FloatField(null = True)

    class Meta:
        db_table = 'ts_daily_futures'
        indexes = [
            models.Index(fields = ['date', 'contract'], name = 'date_future_idx')
        ]
        constraints = [
            models.UniqueConstraint(fields = ['date', 'contract'], name = 'unique_date_future')
        ]
