package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;

import java.util.ArrayList;

import static com.ashwinmenon.www.calcounter.MainActivityFragment.daysToQuery;
import static com.ashwinmenon.www.calcounter.MainActivityFragment.displayFilter;

/**
 * Created by TheAshman on 1/26/2017.
 */

class DayAdapter extends ArrayAdapter<String> {

    public DayAdapter(Activity context, ArrayList<String> w) {
        super(context, android.R.layout.simple_list_item_1, w);
    }

    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        // Check if the existing view is being reused, otherwise inflate the view
        View listItemView = super.getView(position, null, parent);

        // Get the food object located at this position in the list
        if (displayFilter && position < daysToQuery) listItemView.setBackgroundColor(getContext().getResources().getColor(android.R.color.holo_blue_light));

        return listItemView;
    }
}