package com.ashwinmenon.www.calcounter;

/**
 * Simple validation utilities.
 */
public class ValidationUtil {

    /**
     * Check if a string is empty or null.
     */
    public static boolean isEmpty(String text) {
        return text == null || text.trim().isEmpty();
    }

    /**
     * Parse an integer safely, return default if parsing fails.
     */
    public static int parseInt(String text, int defaultValue) {
        try {
            return Integer.parseInt(text);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    /**
     * Check if a value is positive.
     */
    public static boolean isPositive(int value) {
        return value > 0;
    }

    private ValidationUtil() {
        // Prevent instantiation
    }
}
