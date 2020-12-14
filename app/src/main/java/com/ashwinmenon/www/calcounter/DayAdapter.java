package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

import com.ashwinmenon.www.calcounter.db.Day;

import java.util.List;

import static com.ashwinmenon.www.calcounter.MainActivityFragment.daysToQuery;
import static com.ashwinmenon.www.calcounter.MainActivityFragment.displayNutritionAverages;

/**
 * Created by TheAshman on 1/26/2017.
 */

class DayAdapter extends ArrayAdapter<Day> {

    DayAdapter(Activity context, List<Day> days) {
        super(context, android.R.layout.simple_list_item_1, days);
    }

    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        // Check if the existing view is being reused, otherwise inflate the view
        View listItemView = super.getView(position, null, parent);

        // Get the food object located at this position in the list
        if (displayNutritionAverages && position < daysToQuery) {
            listItemView.setBackgroundColor(getContext().getResources().getColor(android.R.color.holo_blue_light));
        }

        Day day = getItem(position);
        TextView textView = (TextView) listItemView;
        textView.setText(day.getDate());

        return listItemView;
    }
}