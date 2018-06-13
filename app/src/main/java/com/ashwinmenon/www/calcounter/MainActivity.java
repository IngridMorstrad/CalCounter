package com.ashwinmenon.www.calcounter;

import android.app.Fragment;
import android.app.FragmentTransaction;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.Menu;
import android.view.MenuItem;

import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.data.LineData;

public class MainActivity extends AppCompatActivity implements MainActivityFragment.OnDaySelectedListener {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Fragment newFragment = new MainActivityFragment();
        FragmentTransaction transaction = getFragmentManager().beginTransaction();

        // Replace whatever is in the fragment_container view with this fragment,
        // and add the transaction to the back stack
        transaction.add(R.id.main_container, newFragment);

        // Commit the transaction
        transaction.commit();
}

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            // Create new fragment and transaction
            Fragment newFragment = new SettingsFragment();
            FragmentTransaction transaction = getFragmentManager().beginTransaction();

            // Replace whatever is in the fragment_container view with this fragment,
            // and add the transaction to the back stack
            transaction.replace(R.id.main_container, newFragment);
            transaction.addToBackStack(null);

            // Commit the transaction
            transaction.commit();
            return true;
        }
        else if (id == R.id.action_chart) {
            Fragment newFragment = new ChartFragment(new LineData(), new Description());
            FragmentTransaction transaction = getFragmentManager().beginTransaction();

            transaction.replace(R.id.main_container, newFragment);
            transaction.addToBackStack(null);

            transaction.commit();
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onDaySelected(int position) {
        FoodFragment foodFragment = (FoodFragment) getFragmentManager().findFragmentById(R.id.food_fragment);
        if (foodFragment != null) {
            // If article frag is available, we're in two-pane layout...

            foodFragment.updatePosition(position);
        } else {
            // Otherwise, we're in the one-pane layout and must swap frags...

            // Create fragment and give it an argument for the selected article
            FoodFragment newFragment = new FoodFragment();
            Bundle args = new Bundle();
            args.putInt(FoodFragment.POSITION_KEY, position);
            newFragment.setArguments(args);

            FragmentTransaction transaction = getFragmentManager().beginTransaction();

            // Replace whatever is in the fragment_container view with this fragment,
            // and add the transaction to the back stack so the user can navigate back
            transaction.replace(R.id.main_container, newFragment);
            transaction.addToBackStack(null);

            // Commit the transaction
            transaction.commit();
        }
    }
}
