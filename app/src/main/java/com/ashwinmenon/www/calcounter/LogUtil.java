package com.ashwinmenon.www.calcounter;

import android.util.Log;

/**
 * Einfaches Logging-Utility für die App.
 */
public class LogUtil {

    private static final String APP_TAG = "CalCounter";

    public static void logInfo(String message) {
        Log.i(APP_TAG, message);
    }

    public static void logError(String message, Throwable error) {
        Log.e(APP_TAG, message, error);
    }

    public static void logDebug(String message) {
        Log.d(APP_TAG, message);
    }
}
