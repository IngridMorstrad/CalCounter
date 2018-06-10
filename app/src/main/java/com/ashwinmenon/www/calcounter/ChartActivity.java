package com.ashwinmenon.www.calcounter;

import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ChartActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chart);
        LineChart chart = findViewById(R.id.chart);
        List<Entry> entries = new ArrayList<>();

        int sz = MainActivityFragment.foods.size();
        int daysToAverageOver = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(this).getString(getString(R.string.key_average),"8"));
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
        LineData lineData = new LineData(dataSet);
        chart.setData(lineData);
        Description description = new Description();
        description.setText("Calorie trend: Calories consumed every " + daysToAverageOver + " days.");
        chart.setDescription(description);
        chart.invalidate();
    }

    private int sumOf(List<Food> integers) {
        int s = 0;
        for (Food f: integers) s+=f.getCaloriesInt();
        return s;
    }
}
