package com.ashwinmenon.www.calcounter;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Simple date utility methods.
 */
public class DateUtil {

    private static final String DATE_FORMAT = "dd/MM/yyyy";

    /**
     * Parse a date string in dd/MM/yyyy format.
     */
    public static Date parseDate(String dateString) throws ParseException {
        SimpleDateFormat format = new SimpleDateFormat(DATE_FORMAT);
        return format.parse(dateString);
    }

    /**
     * Format a date to dd/MM/yyyy string.
     */
    public static String formatDate(Date date) {
        SimpleDateFormat format = new SimpleDateFormat(DATE_FORMAT);
        return format.format(date);
    }

    /**
     * Convert a date to Unix timestamp (seconds).
     */
    public static int dateToTimestamp(Date date) {
        return (int) (date.getTime() / 1000);
    }

    private DateUtil() {
        // Prevent instantiation
    }
}
