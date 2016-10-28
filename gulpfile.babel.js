import autoprefixer from 'autoprefixer'
import concat from 'gulp-concat'
import cssnano from 'cssnano';
import gulp from 'gulp'
import merge from 'merge-stream'
import postcss from 'gulp-postcss'
import pump from 'pump'
import sass from 'gulp-sass'
import uglify from 'gulp-uglify'

var supportedBrowsers = [
  'Chrome >= 50',
  'Firefox >= 46',
  'Explorer >= 11',
  'Safari >= 9',
  'ChromeAndroid >= 50',
  'FirefoxAndroid >= 46'
]

gulp.task('viewflow.scss', () => {
  return gulp.src('./viewflow/frontend/static/viewflow/sass/*.scss')
    .pipe(sass({
      includePaths: ['./node_modules/', './viewflow/frontend/static/viewflow/scss/']
    }).on(
      'error', sass.logError
    ))
    .pipe(postcss([
      autoprefixer({
        browsers: supportedBrowsers
      })
    ]))
    .pipe(gulp.dest(
      './viewflow/frontend/static/viewflow/css/'
    ))
})

gulp.task('default', [
  'viewflow.scss',
])
