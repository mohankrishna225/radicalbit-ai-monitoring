import JobStatus from '@Components/JobStatus';
import { METRICS_TABS } from '@Container/models/Details/constants';
import { JOB_STATUS } from '@Src/constants';
import { useGetReferenceDataQualityQueryWithPolling } from '@State/models/polling-hook';
import { Tabs } from '@radicalbit/radicalbit-design-system';
import { useSearchParams } from 'react-router-dom';
import DataQualityMetrics from './data-quality';
import Imports from './imports';
import ModelQualityMetrics from './model-quality';

const tabs = [
  {
    label: METRICS_TABS.DATA_QUALITIY,
    key: METRICS_TABS.DATA_QUALITIY,
    children: <DataQualityMetrics />,
  },
  {
    label: METRICS_TABS.MODEL_QUALITY,
    key: METRICS_TABS.MODEL_QUALITY,
    children: <ModelQualityMetrics />,
  },
  {
    label: METRICS_TABS.IMPORT,
    key: METRICS_TABS.IMPORT,
    children: <Imports />,
  },

];

export default function ReferenceDashboard() {
  const [searchParams, setSearchParams] = useSearchParams();

  const { data } = useGetReferenceDataQualityQueryWithPolling();
  const jobStatus = data?.jobStatus;

  const activeTab = searchParams.get('tab-metrics') || METRICS_TABS.METRICS;

  const setTab = (value) => {
    searchParams.set('tab-metrics', value);
    setSearchParams(searchParams);
  };

  const onChangeTab = (e) => {
    setTab(e);
  };

  if (jobStatus !== JOB_STATUS.SUCCEEDED) {
    return <JobStatus jobStatus={jobStatus} />;
  }

  return (
    <div className="px-4 pt-4 h-full">
      <Tabs
        activeKey={activeTab}
        fullHeight
        items={tabs}
        onChange={onChangeTab}
      />
    </div>
  );
}
