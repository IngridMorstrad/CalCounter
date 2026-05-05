package com.ashwinmenon.www.calcounter;

/**
 * App-wide constants in one place.
 */
public class AppConstants {

    // Preferences
    public static final String PREF_DAYS_TO_QUERY = "days_to_query";
    public static final String PREF_AVERAGE_DAYS = "average_days";

    // Default values
    public static final int DEFAULT_DAYS_TO_QUERY = 7;
    public static final int DEFAULT_AVERAGE_DAYS = 8;

    // Date format
    public static final String DATE_FORMAT = "dd/MM/yyyy";

    // Start date for tracking
    public static final String START_DATE = "13/10/2020";

    private AppConstants() {
        // Prevent instantiation
    }
}
