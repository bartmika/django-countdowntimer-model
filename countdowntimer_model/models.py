import pytz
from datetime import date, datetime, timedelta

from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from countdowntimer_model.constants import TIMEZONE_CHOICES


class CountdownTimerManager(models.Manager):
    pass


class CountdownTimer(models.Model):
    """
    Abstract model provides data-structure and operations for supporting a
    pausable countdown timer which can be inherited in any Django model.

    How do I start using this model? Just set `duration_in_minutes` when
    creating the object and this model will take care of the test.

    Please note, that if there is an `_` underscore in the function then it
    is supposed to be private, an implementation detail, and should not be used
    as it can change anytime.
    """

    '''
    METADATA
    '''

    class Meta:
        abstract = True

    '''
    CONSTANTS
    '''

    class STATE:
        PAUSED = 1
        RUNNING = 2

    '''
    CHOICES
    '''

    STATE_CHOICES = (
        (STATE.PAUSED, _('Paused')),
        (STATE.RUNNING, _('Running')),
    )

    '''
    SAVED VALUES
    '''

    __original_duration_in_minutes = None

    '''
    OBJECT MANAGERS
    '''

    objects = CountdownTimerManager()

    '''
    MODEL FIELDS
    '''

    # DEVELOPERS NOTE:
    # REQUIRED FILEDS TO SET DURING CREATION OF OBJECT.

    duration_in_minutes = models.PositiveSmallIntegerField(
        _('Duration'),
        help_text=_('The duration to start the countdown timer and proceed to countdown from to zero. Must be in minutes.'),
    )
    state = models.PositiveSmallIntegerField(
        _('State'),
        help_text=_('The state of the countdown timer. Either running or paused.'),
        choices=STATE_CHOICES,
        default=STATE.PAUSED,
        db_index=True,
    )
    timezone_override = models.CharField(
        _("Timezone Override"),
        help_text=_('The timezone override to apply when running the `timezone.now()` function. Leave blank if you do not need to convert timezones.'),
        max_length=63,
        blank=True,
        null=True,
        choices=TIMEZONE_CHOICES
    )
    start_date_offset_in_minutes = models.PositiveSmallIntegerField(
        _('Start date offset in minutes'),
        help_text=_('Add/subtract the duration in minutes the start date of our countdown timer.'),
        default=0,
        blank=True,
    )

    # DEVELOPERS NOTE:
    # IMPLEMENTATION DETAIL FIELDS WHICH ARE MANAGED BY OUR MODEL. DO NOT SET
    # THESE FEILD EVER.

    paused_at = models.DateTimeField(
        _("Paused at"),
        help_text=_('The date and time this countdown timer was paused at.'),
        blank=True,
        editable=False,
        null=True
    )
    cumulative_pause_duration = models.DurationField(
        _("Cumulative Pause Duration"),
        help_text=_('The cumulative of all timedeltas caused by pauses in our timer.'),
        default=timedelta,
        blank=True,
        editable=False,
    )
    original_start_at = models.DateTimeField(
        _("Original start at"),
        help_text=_('The original date/time this countdown timer began.'),
        editable=False,
    )
    original_end_at = models.DateTimeField(
        _("Original end at"),
        help_text=_('The original date/time this countdown timer will finish by.'),
        editable=False,
    )
    modified_start_at = models.DateTimeField(
        _("Modified start at"),
        help_text=_('The original date/time plus cumulative pause duration.'),
        editable=False,
    )
    modified_end_at = models.DateTimeField(
        _("Modified end at"),
        help_text=_('The original date/time plus cumulative pause duration.'),
        null=True,
        blank=True,
        editable=False,
    )


    """
    MODEL FUNCTIONS
    """

    def __init__(self, *args, **kwargs):
        """
        Override the ``init`` function to support our custom code.
        """
        super(CountdownTimer, self).__init__(*args, **kwargs)
        self.__original_duration_in_minutes = self.duration_in_minutes

    @transaction.atomic
    def save(self, *args, **kwargs):
        '''
        Override the `save` function to support our custom code.
        '''
        # Declare variable we will use often in this function.
        now_dt = self._now_dt()

        '''
        Reset countdown timer if a new ``duration_in_minutes`` value has been
        set by the user. As a result all previously set values will be erased.
        '''
        if self.duration_in_minutes != self.__original_duration_in_minutes:
            self.original_start_at = None
            self.paused_at = None
            self.cumulative_pause_duration = timedelta()

        '''
        Assign our initial values since they were not set.
        '''
        if self.original_start_at == None:
            self.original_start_at = now_dt + timedelta(minutes=self.start_date_offset_in_minutes)
            self.original_end_at = self.original_start_at + timedelta(minutes=self.duration_in_minutes)

        # CASE 1 OF 2: Becaming a paused state
        if self.state == self.STATE.PAUSED:
            if self.paused_at == None:
                self.paused_at = now_dt

        # CASE 2 OF 2: No longer in paused state
        else:
            if self.paused_at:
                self.cumulative_pause_duration = self.cumulative_pause_duration + self._pause_delta()
                self.paused_at = None  # Reset our reset datetime.

        '''
        Reset our modified date/times so the calculations performed by this
        model to take into account our cumulative paused duration value.
        '''
        self.modified_start_at = self.original_start_at + self.cumulative_pause_duration
        self.modified_end_at = self.original_end_at + self.cumulative_pause_duration

        '''
        Finally call the parent function which handles saving so we can carry
        out the saving operation by Django in our ORM.
        '''
        super(CountdownTimer, self).save(*args, **kwargs)
        self.__original_duration_in_minutes = self.duration_in_minutes

    def _now_dt(self):
        # Apply timezone override if user requested it.
        if self.timezone_override:
            timezone_override = pytz.timezone(self.timezone_override)
            utc_dt = datetime.utcnow().replace(tzinfo=pytz.utc)
            return utc_dt.astimezone(timezone_override)
        else:
            return datetime.utcnow().replace(tzinfo=pytz.utc)

    def _pause_delta(self):
        """
        Returns how much `timedelta` changed since we paused our countdown timer.
        """
        if self.paused_at:
            now = self._now_dt()
            _pause_delta = now - self.paused_at
            return _pause_delta
        return timedelta()

    def _cumulative_pause_duration_in_minutes(self):
        """
        Helper function to return our `cumulative_pause_duration` value
        in a `minutes` unit of measure.
        """
        return round(abs(self.cumulative_pause_duration.seconds / 60))

    def _conditional_pause_delta(self):
        """
        Returns how much `timedelta` changed since we paused our countdown
        timer only if the state of our is set to `PAUSED`.
        """
        if self.state == self.STATE.PAUSED:
            now = self._now_dt()
            _pause_delta = now - self.paused_at
            return _pause_delta
        return timedelta()

    def remaining_time(self):
        """
        Returns how much time is remaining in `time` format while ignoring
        the time that elasped due to our pausing.
        """
        try:
            '''
            DEVELOPERS NOTE:
            IF your code has tenancy and you want to get 'now' specific to a
            tenant then call that tenants `aware_now_dt` function. If you do not
            want this feature then the default `now` will be returned.
            '''
            now_dt = self.tenant.aware_now_dt()
        except Exception as e:
            now_dt = self._now_dt()
        end_dt = self._conditional_pause_delta() + self.modified_end_at

        if now_dt > end_dt:
            return timedelta(0)
        return end_dt - now_dt

    def remaining_time_in_minutes(self):
        """
        Returns how much time is remaining in `integer` format using
        the `minutes` unit of measure.
        """
        return round(abs(self.remaining_time().seconds / 60))

    def remaining_future_datetime(self):
        """
        Returns the current date time plus the remaining time in minutes.
        This is a useful function if your countdown timer GUI wants a date/time
        value to start the GUI countdown timer instance.
        """
        remaining_time_in_minutes = self.remaining_time_in_minutes()
        return self._now_dt() + timedelta(minutes=remaining_time_in_minutes)

    def time_elapsed(self):
        """
        Returns how much time elapsed in `time` format.
        (Ignores duration lost due to pauses)
        """
        now_dt = self._now_dt()
        start_dt = self._conditional_pause_delta() + self.original_start_at

        if start_dt > now_dt:
            return timedelta(0)
        return now_dt - start_dt

    def time_elapsed_in_minutes(self):
        """
        Returns how much time elapsed in `integer` format using the `minutes`
        unit of measure.
        """
        return round(abs(self.time_elapsed().seconds / 60))

    def time_elapsed_since_beginning(self):
        """
        Returns how much time elapsed since the beginning in `time` format.
        (This function includes pause time.)
        """
        now_dt = self._now_dt()
        start_dt = self.original_start_at

        if start_dt > now_dt:
            return timedelta(0)
        return now_dt - start_dt

    def time_elapsed_since_beginning_in_minutes(self):
        """
        Returns how much time elapsed since the beginning in `integer` format
        using the `minutes` unit of measure.
        (This function includes pause time.)
        """
        return round(abs(self.time_elapsed_since_beginning().seconds / 60))
