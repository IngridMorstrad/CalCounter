package com.ashwinmenon.www.calcounter;

import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import com.ashwinmenon.www.calcounter.db.Food;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

public class ChartFragment extends Fragment {

    private LineData lineData;
    private Description description;

    public ChartFragment() {
        // Required empty public constructor for Fragment
    }

    public static ChartFragment newInstance() {
        return new ChartFragment();
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        lineData = new LineData();
        description = new Description();

        List<Entry> entries = new ArrayList<>();

        int sz = MainActivityFragment.foodsForAllDays.size();
        int daysToAverageOver = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(requireActivity()).getString(getString(R.string.key_average), "8"));
        int daysToDisplay = 14;
        int currCalSum = 0;
        for (int i = 1; i <= Math.min(sz, daysToAverageOver * daysToDisplay); i++) {
            currCalSum += sumOf(MainActivityFragment.foodsForAllDays.get(sz - i));
            if (i % daysToAverageOver == 0) {
                entries.add(new Entry(daysToDisplay - i / daysToAverageOver + 1, (float) currCalSum / daysToAverageOver));
                currCalSum = 0;
            }
        }

        Collections.reverse(entries);
        LineDataSet dataSet = new LineDataSet(entries, "Calories");
        lineData.addDataSet(dataSet);
        description.setText("Calorie trend: Calories consumed every " + daysToAverageOver + " days.");
        description.setTextSize(12);
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View rootView = inflater.inflate(R.layout.activity_chart, container, false);
        LineChart chart = rootView.findViewById(R.id.chart);
        chart.setData(lineData);
        chart.setDescription(description);
        chart.invalidate();
        return rootView;
    }

    private int sumOf(List<Food> foods) {
        int s = 0;
        for (Food f : foods) s += f.getCalories();
        return s;
    }
}
