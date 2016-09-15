package org.apache.mesos.state;


import org.apache.curator.test.TestingServer;
import org.apache.mesos.curator.CuratorStateStore;
import org.apache.mesos.testutils.TestConstants;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class SchedulerStateTest {
    private static final String ROOT_ZK_PATH = "/test-root-path";
    private static TestingServer testZk;

    private SchedulerState schedulerState;

    @BeforeClass
    public static void beforeAll() throws Exception {
        testZk = new TestingServer();
    }

    @Before
    public void beforeEach() {
        schedulerState = new SchedulerState(new CuratorStateStore(ROOT_ZK_PATH, testZk.getConnectString()));
    }

    @Test
    public void testGetFrameworkId() {
        schedulerState.setFrameworkId(TestConstants.frameworkId);
        assertEquals(schedulerState.getFrameworkId().get(), TestConstants.frameworkId);
    }

    @Test
    public void testIsSuppressed() {
        schedulerState.setSuppressed(true);
        assertTrue(schedulerState.isSuppressed());
        schedulerState.setSuppressed(false);
        assertTrue(!schedulerState.isSuppressed());
    }
}
