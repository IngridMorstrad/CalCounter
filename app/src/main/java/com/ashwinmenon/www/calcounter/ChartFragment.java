package com.ashwinmenon.www.calcounter;

import android.app.Fragment;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class ChartFragment extends Fragment {

    @NonNull
    private final LineData lineData;
    @NonNull
    private final Description description;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        List<Entry> entries = new ArrayList<>();

        int sz = MainActivityFragment.foods.size();
        int daysToAverageOver = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(getActivity()).getString(getString(R.string.key_average),"8"));
        int daysToDisplay = 14;
        int currCalSum = 0;
        for (int i = 1; i <= Math.min(sz,daysToAverageOver*daysToDisplay); i++) {
            currCalSum += sumOf(MainActivityFragment.foods.get(sz-i));
            if (i%daysToAverageOver == 0) {
                entries.add(new Entry(daysToDisplay-i/daysToAverageOver+1, (float)currCalSum/daysToAverageOver));
                currCalSum = 0;
            }
        }

        // needs to be sorted by x to work correctly
        Collections.reverse(entries);
        LineDataSet dataSet = new LineDataSet(entries, "Calories"); // add entries to dataset
        lineData.addDataSet(dataSet);
        description.setText("Calorie trend: Calories consumed every " + daysToAverageOver + " days.");
        description.setTextSize(12);
    }

    @Nullable
    @Override
    public View onCreateView(LayoutInflater inflater, @Nullable ViewGroup container, Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.activity_chart, container, false);
        LineChart chart = rootView.findViewById(R.id.chart);
        chart.setData(lineData);
        chart.setDescription(description);
        chart.invalidate();
        return rootView;
    }

    private int sumOf(List<Food> integers) {
        int s = 0;
        for (Food f: integers) s+=f.getCaloriesInt();
        return s;
    }
}
