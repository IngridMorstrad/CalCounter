package com.ashwinmenon.www.calcounter;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v4.app.Fragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

/**
 * A placeholder fragment containing a simple view.
 */
public class MainActivityFragment extends Fragment {

    Integer carbs, fats, proteins, cals;
    String errors;

    public MainActivityFragment() {
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(getActivity());
        errors = "";

        try {
            carbs = Integer.parseInt(prefs.getString(getString(R.string.carbs_key), getString(R.string.carbs_default)));
        }
        catch (InstantiationException e) {
            errors += "Invalid value for carbs\n";
        }
        try {
            fats = Integer.parseInt(prefs.getString(getString(R.string.fats_key), getString(R.string.fats_default)));
        }
        catch (InstantiationException e) {
            errors = "Invalid value for fats\n";
        }
        try {
            proteins = Integer.parseInt(prefs.getString(getString(R.string.proteins_key), getString(R.string.proteins_default)));
        }
        catch (InstantiationException e) {
            errors = "Invalid value for proteins\n";
        }

        super.onCreate(savedInstanceState);
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.fragment_main, container, false);
        TextView carbsView = (TextView) rootView.findViewById(R.id.carbs);
        TextView fatsView = (TextView) rootView.findViewById(R.id.fats);
        TextView proteinsView = (TextView) rootView.findViewById(R.id.proteins);
        TextView calsView = (TextView) rootView.findViewById(R.id.calories);

        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(getActivity());

        if (errors.isEmpty()) {
            carbsView.setText(carbs.toString());
            fatsView.setText(fats.toString());
            proteinsView.setText(proteins.toString());
            cals = carbs*4 + fats*9 + proteins*4;
            calsView.setText(cals.toString());
        }
        else {
            carbsView.setText("ERROR");
            fatsView.setText("ERROR");
            proteinsView.setText("ERROR");
            calsView.setText("ERROR");
        }

        return rootView;
    }
}
