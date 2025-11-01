"""
Unit tests for FlatFileFetcher class
Tests data fetching from Polygon.io Flat Files using mocked S3 responses
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import gzip
from io import BytesIO, StringIO
from botocore.exceptions import ClientError, NoCredentialsError

from flatfile_fetcher import FlatFileFetcher, DARK_POOL_EXCHANGE_ID


class TestFlatFileFetcherInit(unittest.TestCase):
    """Test FlatFileFetcher initialization"""

    @patch('flatfile_fetcher.Config')
    def test_init_with_valid_credentials(self, mock_config):
        """Test successful initialization with valid credentials"""
        mock_config.POLYGON_S3_ACCESS_KEY = 'test_key'
        mock_config.POLYGON_S3_SECRET_KEY = 'test_secret'
        mock_config.DATA_DIR = '/tmp/test'

        with patch('flatfile_fetcher.boto3.client') as mock_boto3:
            fetcher = FlatFileFetcher()

            mock_boto3.assert_called_once_with(
                's3',
                aws_access_key_id='test_key',
                aws_secret_access_key='test_secret',
                region_name='us-east-1',
                endpoint_url='https://files.polygon.io'
            )
            self.assertEqual(fetcher.bucket, 'flatfiles')

    @patch('flatfile_fetcher.Config')
    def test_init_without_credentials_raises_error(self, mock_config):
        """Test initialization fails without credentials"""
        mock_config.POLYGON_S3_ACCESS_KEY = None
        mock_config.POLYGON_S3_SECRET_KEY = None

        with self.assertRaises(ValueError) as context:
            FlatFileFetcher()

        self.assertIn('S3 credentials not set', str(context.exception))


class TestFetchDailyAggregates(unittest.TestCase):
    """Test fetch_daily_aggregates method"""

    def setUp(self):
        """Set up test fixtures"""
        self.patcher_config = patch('flatfile_fetcher.Config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.POLYGON_S3_ACCESS_KEY = 'test_key'
        self.mock_config.POLYGON_S3_SECRET_KEY = 'test_secret'
        self.mock_config.DATA_DIR = '/tmp/test'

        self.patcher_boto3 = patch('flatfile_fetcher.boto3.client')
        self.mock_boto3 = self.patcher_boto3.start()

        self.patcher_db = patch('flatfile_fetcher.db')
        self.mock_db = self.patcher_db.start()

        self.fetcher = FlatFileFetcher()
        self.test_date = date(2025, 1, 15)

    def tearDown(self):
        """Clean up patches"""
        self.patcher_config.stop()
        self.patcher_boto3.stop()
        self.patcher_db.stop()

    def _create_mock_csv_data(self, rows):
        """Helper to create mock gzipped CSV data"""
        csv_content = "ticker,volume,open,close,high,low,transactions\n"
        for row in rows:
            csv_content += f"{row['ticker']},{row['volume']},{row['open']},{row['close']},{row['high']},{row['low']},{row['transactions']}\n"

        gzipped = gzip.compress(csv_content.encode('utf-8'))
        return gzipped

    def test_fetch_daily_aggregates_success(self):
        """Test successful fetch of daily aggregates"""
        # Create mock CSV data
        test_data = [
            {'ticker': 'AAPL', 'volume': 1000000, 'open': 150.0, 'close': 152.0, 'high': 153.0, 'low': 149.0, 'transactions': 5000},
            {'ticker': 'GOOGL', 'volume': 500000, 'open': 2800.0, 'close': 2820.0, 'high': 2830.0, 'low': 2790.0, 'transactions': 3000}
        ]
        mock_gzipped_data = self._create_mock_csv_data(test_data)

        # Mock S3 response
        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        # Mock database session
        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        count = self.fetcher.fetch_daily_aggregates(self.test_date)

        # Verify
        self.assertEqual(count, 2)
        self.fetcher.s3_client.get_object.assert_called_once()
        self.assertEqual(mock_session.add.call_count, 2)
        mock_session.commit.assert_called()
        self.mock_db.close_session.assert_called_once()

    def test_fetch_daily_aggregates_updates_existing(self):
        """Test updating existing records in database"""
        test_data = [
            {'ticker': 'AAPL', 'volume': 1000000, 'open': 150.0, 'close': 152.0, 'high': 153.0, 'low': 149.0, 'transactions': 5000}
        ]
        mock_gzipped_data = self._create_mock_csv_data(test_data)

        # Mock S3 response
        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        # Mock database session with existing record
        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        existing_record = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_record

        # Execute
        count = self.fetcher.fetch_daily_aggregates(self.test_date)

        # Verify existing record was updated
        self.assertEqual(count, 1)
        self.assertEqual(existing_record.volume, 1000000)
        self.assertEqual(existing_record.close, 152.0)
        mock_session.commit.assert_called()

    def test_fetch_daily_aggregates_access_denied(self):
        """Test handling of access denied errors"""
        error_response = {'Error': {'Code': '403'}}
        self.fetcher.s3_client.get_object = Mock(
            side_effect=ClientError(error_response, 'GetObject')
        )

        with self.assertRaises(ClientError):
            self.fetcher.fetch_daily_aggregates(self.test_date)

    def test_fetch_daily_aggregates_no_credentials(self):
        """Test handling of missing credentials"""
        self.fetcher.s3_client.get_object = Mock(side_effect=NoCredentialsError())

        with self.assertRaises(NoCredentialsError):
            self.fetcher.fetch_daily_aggregates(self.test_date)

    def test_fetch_daily_aggregates_correct_s3_path(self):
        """Test that the correct S3 path is constructed"""
        mock_response = {'Body': BytesIO(gzip.compress(b"ticker,volume,open,close,high,low,transactions\n"))}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session

        self.fetcher.fetch_daily_aggregates(self.test_date)

        # Verify correct S3 path
        expected_key = 'us_stocks_sip/day_aggs_v1/2025/01/2025-01-15.csv.gz'
        self.fetcher.s3_client.get_object.assert_called_once_with(
            Bucket='flatfiles',
            Key=expected_key
        )


class TestFetchTradesAndAggregate(unittest.TestCase):
    """Test fetch_trades_and_aggregate method"""

    def setUp(self):
        """Set up test fixtures"""
        self.patcher_config = patch('flatfile_fetcher.Config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.POLYGON_S3_ACCESS_KEY = 'test_key'
        self.mock_config.POLYGON_S3_SECRET_KEY = 'test_secret'
        self.mock_config.DATA_DIR = '/tmp/test'

        self.patcher_boto3 = patch('flatfile_fetcher.boto3.client')
        self.mock_boto3 = self.patcher_boto3.start()

        self.patcher_db = patch('flatfile_fetcher.db')
        self.mock_db = self.patcher_db.start()

        self.fetcher = FlatFileFetcher()
        self.test_date = date(2025, 1, 15)

    def tearDown(self):
        """Clean up patches"""
        self.patcher_config.stop()
        self.patcher_boto3.stop()
        self.patcher_db.stop()

    def _create_mock_trades_csv(self, trades):
        """Helper to create mock gzipped trades CSV data"""
        csv_content = "ticker,exchange,trf_id,size,price\n"
        for trade in trades:
            csv_content += f"{trade['ticker']},{trade['exchange']},{trade['trf_id']},{trade['size']},{trade['price']}\n"

        gzipped = gzip.compress(csv_content.encode('utf-8'))
        return gzipped

    def test_fetch_trades_dark_pool_only(self):
        """Test fetching only dark pool trades"""
        # Create mock trades data with dark pool and non-dark pool trades
        test_trades = [
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF1', 'size': 1000, 'price': 150.0},  # Dark pool
            {'ticker': 'AAPL', 'exchange': 1, 'trf_id': '', 'size': 500, 'price': 151.0},  # Not dark pool
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF2', 'size': 800, 'price': 152.0},  # Dark pool
        ]
        mock_gzipped_data = self._create_mock_trades_csv(test_trades)

        # Mock S3 response
        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        # Mock database session
        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        count = self.fetcher.fetch_trades_and_aggregate(self.test_date, dark_pool_only=True)

        # Verify only dark pool trades were counted
        self.assertEqual(count, 1)  # Only one ticker (AAPL)
        mock_session.add.assert_called_once()

        # Verify the aggregated values
        added_record = mock_session.add.call_args[0][0]
        self.assertEqual(added_record.ticker, 'AAPL')
        self.assertEqual(added_record.volume, 1800)  # 1000 + 800 (only dark pool trades)
        self.assertEqual(added_record.transactions, 2)  # 2 dark pool trades

    def test_fetch_trades_min_trade_size_filter(self):
        """Test filtering trades by minimum size"""
        test_trades = [
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF1', 'size': 50, 'price': 150.0},  # Below min
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF2', 'size': 150, 'price': 151.0},  # Above min
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF3', 'size': 200, 'price': 152.0},  # Above min
        ]
        mock_gzipped_data = self._create_mock_trades_csv(test_trades)

        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute with min_trade_size=100
        count = self.fetcher.fetch_trades_and_aggregate(
            self.test_date,
            dark_pool_only=True,
            min_trade_size=100
        )

        # Verify only trades >= 100 were counted
        added_record = mock_session.add.call_args[0][0]
        self.assertEqual(added_record.volume, 350)  # 150 + 200
        self.assertEqual(added_record.transactions, 2)

    def test_fetch_trades_multiple_tickers(self):
        """Test aggregating trades for multiple tickers"""
        test_trades = [
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF1', 'size': 1000, 'price': 150.0},
            {'ticker': 'GOOGL', 'exchange': 4, 'trf_id': 'TRF2', 'size': 500, 'price': 2800.0},
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF3', 'size': 800, 'price': 151.0},
        ]
        mock_gzipped_data = self._create_mock_trades_csv(test_trades)

        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        count = self.fetcher.fetch_trades_and_aggregate(self.test_date, dark_pool_only=True)

        # Verify both tickers were processed
        self.assertEqual(count, 2)
        self.assertEqual(mock_session.add.call_count, 2)

    def test_fetch_trades_calculates_high_low(self):
        """Test that high and low prices are calculated correctly"""
        test_trades = [
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF1', 'size': 100, 'price': 150.0},
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF2', 'size': 100, 'price': 155.0},  # High
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': 'TRF3', 'size': 100, 'price': 148.0},  # Low
        ]
        mock_gzipped_data = self._create_mock_trades_csv(test_trades)

        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        self.fetcher.fetch_trades_and_aggregate(self.test_date, dark_pool_only=True)

        # Verify high/low prices
        added_record = mock_session.add.call_args[0][0]
        self.assertEqual(added_record.high, 155.0)
        self.assertEqual(added_record.low, 148.0)

    def test_fetch_trades_correct_s3_path(self):
        """Test that the correct S3 path is constructed for trades"""
        mock_response = {'Body': BytesIO(gzip.compress(b"ticker,exchange,trf_id,size,price\n"))}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session

        self.fetcher.fetch_trades_and_aggregate(self.test_date)

        # Verify correct S3 path
        expected_key = 'us_stocks_sip/trades_v1/2025/01/2025-01-15.csv.gz'
        self.fetcher.s3_client.get_object.assert_called_once_with(
            Bucket='flatfiles',
            Key=expected_key
        )


class TestBackfillData(unittest.TestCase):
    """Test backfill_data method"""

    def setUp(self):
        """Set up test fixtures"""
        self.patcher_config = patch('flatfile_fetcher.Config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.POLYGON_S3_ACCESS_KEY = 'test_key'
        self.mock_config.POLYGON_S3_SECRET_KEY = 'test_secret'
        self.mock_config.DATA_DIR = '/tmp/test'
        self.mock_config.USE_TRADES_FILES = False
        self.mock_config.DARK_POOL_ONLY = True
        self.mock_config.MIN_TRADE_SIZE = 100

        self.patcher_boto3 = patch('flatfile_fetcher.boto3.client')
        self.mock_boto3 = self.patcher_boto3.start()

        self.fetcher = FlatFileFetcher()

    def tearDown(self):
        """Clean up patches"""
        self.patcher_config.stop()
        self.patcher_boto3.stop()

    @patch('flatfile_fetcher.datetime')
    def test_backfill_skips_weekends(self, mock_datetime):
        """Test that backfill skips weekend dates"""
        # Set today as Monday, January 20, 2025
        mock_datetime.now.return_value = datetime(2025, 1, 20)

        with patch.object(self.fetcher, 'fetch_daily_aggregates') as mock_fetch:
            self.fetcher.backfill_data(days=7)

            # Should only be called for weekdays
            # From Jan 13 (Mon) to Jan 20 (Mon): 6 weekdays
            self.assertEqual(mock_fetch.call_count, 6)

    @patch('flatfile_fetcher.datetime')
    def test_backfill_uses_trades_when_configured(self, mock_datetime):
        """Test that backfill uses trades files when configured"""
        mock_datetime.now.return_value = datetime(2025, 1, 20)
        self.mock_config.USE_TRADES_FILES = True

        with patch.object(self.fetcher, 'fetch_trades_and_aggregate') as mock_fetch_trades:
            with patch.object(self.fetcher, 'fetch_daily_aggregates') as mock_fetch_aggs:
                self.fetcher.backfill_data(days=3)

                # Should use trades files
                self.assertGreater(mock_fetch_trades.call_count, 0)
                self.assertEqual(mock_fetch_aggs.call_count, 0)

    @patch('flatfile_fetcher.datetime')
    def test_backfill_handles_errors_gracefully(self, mock_datetime):
        """Test that backfill continues on errors"""
        # Set to Friday Jan 17, 2025 for easier testing (all weekdays)
        mock_datetime.now.return_value = datetime(2025, 1, 17)

        with patch.object(self.fetcher, 'fetch_daily_aggregates') as mock_fetch:
            # Make some calls fail
            mock_fetch.side_effect = [
                100,  # Success
                Exception("S3 error"),  # Failure
                150,  # Success
            ]

            # Should not raise exception
            # Backfill 2 days: Jan 15 (Wed), 16 (Thu), 17 (Fri) = 3 weekdays
            self.fetcher.backfill_data(days=2)

            # Should have attempted all weekdays
            self.assertEqual(mock_fetch.call_count, 3)


class TestDarkPoolIdentification(unittest.TestCase):
    """Test dark pool identification logic"""

    def test_dark_pool_exchange_id_constant(self):
        """Test that dark pool exchange ID is correctly defined"""
        self.assertEqual(DARK_POOL_EXCHANGE_ID, 4)

    def setUp(self):
        """Set up test fixtures"""
        self.patcher_config = patch('flatfile_fetcher.Config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.POLYGON_S3_ACCESS_KEY = 'test_key'
        self.mock_config.POLYGON_S3_SECRET_KEY = 'test_secret'
        self.mock_config.DATA_DIR = '/tmp/test'

        self.patcher_boto3 = patch('flatfile_fetcher.boto3.client')
        self.mock_boto3 = self.patcher_boto3.start()

        self.patcher_db = patch('flatfile_fetcher.db')
        self.mock_db = self.patcher_db.start()

        self.fetcher = FlatFileFetcher()
        self.test_date = date(2025, 1, 15)

    def tearDown(self):
        """Clean up patches"""
        self.patcher_config.stop()
        self.patcher_boto3.stop()
        self.patcher_db.stop()

    def test_dark_pool_requires_both_exchange_and_trf(self):
        """Test that dark pool identification requires exchange=4 AND trf_id"""
        test_trades = [
            {'ticker': 'AAPL', 'exchange': 4, 'trf_id': '', 'size': 100, 'price': 150.0},  # No trf_id
            {'ticker': 'GOOGL', 'exchange': 1, 'trf_id': 'TRF1', 'size': 100, 'price': 2800.0},  # Wrong exchange
            {'ticker': 'MSFT', 'exchange': 4, 'trf_id': 'TRF2', 'size': 100, 'price': 400.0},  # Valid dark pool
        ]

        csv_content = "ticker,exchange,trf_id,size,price\n"
        for trade in test_trades:
            csv_content += f"{trade['ticker']},{trade['exchange']},{trade['trf_id']},{trade['size']},{trade['price']}\n"

        mock_gzipped_data = gzip.compress(csv_content.encode('utf-8'))
        mock_response = {'Body': BytesIO(mock_gzipped_data)}
        self.fetcher.s3_client.get_object = Mock(return_value=mock_response)

        mock_session = MagicMock()
        self.mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        count = self.fetcher.fetch_trades_and_aggregate(self.test_date, dark_pool_only=True)

        # Only MSFT should be counted (has both exchange=4 and trf_id)
        self.assertEqual(count, 1)
        added_record = mock_session.add.call_args[0][0]
        self.assertEqual(added_record.ticker, 'MSFT')


if __name__ == '__main__':
    unittest.main()
